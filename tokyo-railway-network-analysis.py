# =========================================================
# Tokyo 23 wards railway stations
# =========================================================

import warnings
warnings.filterwarnings("ignore")

import re
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
import statsmodels.api as sm

from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from matplotlib.lines import Line2D


# =========================================================
# 0. PATH
# =========================================================
P_ST = r"C:/Users/2lluc/Desktop/tokyo-railway-network-analysis/data/N05-17_Station2.shp"
P_SEC = r"C:/Users/2lluc/Desktop/tokyo-railway-network-analysis/data/N05-17_RailroadSection2.shp"
P_WARD = r"C:/Users/2lluc/Desktop/tokyo-railway-network-analysis/data/N03-23_13_230101.shp"
P_RID = r"C:/Users/2lluc/Desktop/tokyo-railway-network-analysis/data/S12-18_NumberOfPassengers.shp"
P_JU = r"C:/Users/2lluc/Desktop/tokyo-railway-network-analysis/data/ju01.xlsx"


# =========================================================
# 1. CONFIG
# =========================================================
RID_COL = "S12_033"   # 2017
Y_COLS = ["S12_009", "S12_013", "S12_017", "S12_021", "S12_025", "S12_029", "S12_033"]
Y_MAP = {
    2011: "S12_009",
    2012: "S12_013",
    2013: "S12_017",
    2014: "S12_021",
    2015: "S12_025",
    2016: "S12_029",
    2017: "S12_033",
}

TARGET_YEAR = 2015
KEEP_OP = {2, 3, 4, 5}

DB_EPS = 50
LINE_BUF = 160
MIN_SEG = 30

ALPHA = 0.62
STEPS = 25

TAU = 800.0
W_MIN = 0.70
W_MAX = 0.95

MEGA_N = 12
HUB_Q = 0.97
MAX_HOP = 2
LOCAL_EPS = 1.0

GMM_K = 12
RAND = 42

TOKYO23 = [
    "千代田区","中央区","港区","新宿区","文京区","台東区","墨田区","江東区",
    "品川区","目黒区","大田区","世田谷区","渋谷区","中野区","杉並区","豊島区",
    "北区","荒川区","板橋区","練馬区","足立区","葛飾区","江戸川区"
]


# =========================================================
# 2. HELPER
# =========================================================
def norm_station(x):
    x = str(x).strip()
    x = re.sub(r"\s+", "", x)
    x = x.replace("ヶ", "ケ")
    x = re.sub(r"[（(].*?[)）]", "", x)
    x = re.sub(r"[〈<].*?[>〉]", "", x)
    return x


def norm_line(x):
    x = str(x) if x is not None else ""
    x = x.strip()
    x = re.sub(r"\s+", "", x)
    x = re.sub(r"^\d+号線", "", x)
    x = re.sub(r"[（(].*?[)）]", "", x)
    x = x.replace("赤羽線", "埼京線")
    return x


def take_name(x):
    x = str(x).strip()
    if "_" in x:
        return x.split("_", 1)[1].strip()
    return x


def z(s):
    s = pd.to_numeric(pd.Series(s), errors="coerce").astype(float)
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)


def z_clip(s, q1=0.01, q2=0.99):
    s = pd.to_numeric(pd.Series(s), errors="coerce").astype(float)
    lo = s.quantile(q1)
    hi = s.quantile(q2)
    s = s.clip(lo, hi)
    return z(s)


def mk_sizes(s, smin=20, smax=350, mode="sqrt", q1=0.02, q2=0.98):
    x = pd.to_numeric(s, errors="coerce").astype(float).fillna(0.0)
    lo = x.quantile(q1)
    hi = x.quantile(q2)
    x = x.clip(lo, hi)

    if mode == "sqrt":
        x = np.sqrt(np.clip(x, 0, None))
    elif mode == "log":
        x = np.log1p(np.clip(x, 0, None))

    x = (x - x.min()) / (x.max() - x.min() + 1e-9)
    return smin + x * (smax - smin)


def slope(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = ~np.isnan(y)
    if m.sum() < 2:
        return np.nan
    x = x[m]
    y = y[m]
    return np.polyfit(x, y, 1)[0]


def get_other_ward(pt, own, ward_gdf):
    best_w = None
    best_d = np.inf
    for _, r in ward_gdf.iterrows():
        w = r["ward"]
        if w == own:
            continue
        d = pt.distance(r.geometry)
        if d < best_d:
            best_d = d
            best_w = w
    return best_w, float(best_d)


def mix_w(dist, tau=800.0, wmin=0.70, wmax=0.95):
    x = 1 - np.exp(-dist / tau)
    w = wmin + (wmax - wmin) * x
    return float(np.clip(w, wmin, wmax))


def mix_val(v1, v2, w):
    if pd.isna(v1) and pd.isna(v2):
        return np.nan
    if pd.isna(v1):
        return v2
    if pd.isna(v2):
        return v1
    return w * v1 + (1 - w) * v2


def neigh_stats(df, G, col):
    val = df.set_index("node_id")[col].to_dict()
    mean_lst, med_lst, max_lst = [], [], []

    for nid in df["node_id"]:
        nb = list(G.neighbors(nid)) if nid in G else []
        vs = pd.Series([val.get(x, np.nan) for x in nb], dtype=float).dropna()
        if len(vs) == 0:
            mean_lst.append(np.nan)
            med_lst.append(np.nan)
            max_lst.append(np.nan)
        else:
            mean_lst.append(vs.mean())
            med_lst.append(vs.median())
            max_lst.append(vs.max())

    return (
        pd.Series(mean_lst, index=df.index),
        pd.Series(med_lst, index=df.index),
        pd.Series(max_lst, index=df.index),
    )


def hub_exposure(df, G, rid_col, q=0.97, max_hop=2):
    log_r = np.log1p(pd.to_numeric(df[rid_col], errors="coerce").fillna(0.0))
    cut = log_r.quantile(q)
    betz = z_clip(df["betweenness"]).fillna(0.0)

    hubs = set(
        df.loc[
            (log_r >= cut) | (df["n_lines"] >= 5) | (betz >= 1.5),
            "node_id"
        ].tolist()
    )

    rid_d = df.set_index("node_id")[rid_col].to_dict()
    bet_d = df.set_index("node_id")["betweenness"].to_dict()
    line_d = df.set_index("node_id")["n_lines"].to_dict()

    rmax = max(rid_d.values()) if len(rid_d) else 1.0
    bmax = df["betweenness"].max() + 1e-9
    lmax = df["n_lines"].max() + 1e-9

    out = []
    for nid in df["node_id"]:
        e = 0.0
        if nid in hubs:
            e += (
                0.80
                + 0.15 * np.log1p(rid_d.get(nid, 0.0)) / np.log1p(rmax + 1.0)
                + 0.05 * line_d.get(nid, 0.0) / lmax
            )

        lengths = nx.single_source_shortest_path_length(G, nid, cutoff=max_hop)
        for other, hop in lengths.items():
            if other == nid or other not in hubs:
                continue

            if hop == 1:
                w = 1.25
            elif hop == 2:
                w = 0.45
            else:
                w = 0.0

            e += w * (
                0.55 * np.log1p(rid_d.get(other, 0.0)) / np.log1p(rmax + 1.0)
                + 0.30 * bet_d.get(other, 0.0) / bmax
                + 0.15 * line_d.get(other, 0.0) / lmax
            )
        out.append(e)

    return pd.Series(out, index=df.index), hubs


def get_role_colors():
    return {
        "Mega Hub": "#d95f5f",
        "CBD": "#4c78a8",
        "Transfer Hub": "#e39c37",
        "Sub-center": "#8c6bb1",
        "Residential": "#4f9d69",
    }


def get_line_colors():
    return {
        "銀座線": "#F39700",
        "丸ノ内線": "#E60012",
        "日比谷線": "#9CAEB7",
        "東西線": "#00A7DB",
        "千代田線": "#009944",
        "有楽町線": "#D7C447",
        "半蔵門線": "#8F76D6",
        "南北線": "#00AC9B",
        "副都心線": "#C60F7B",
        "浅草線": "#E85298",
        "三田線": "#0079C2",
        "新宿線": "#6CBB5A",
        "大江戸線": "#B6007A",
        "日暮里・舎人線": "#FF9900",
        "ゆりかもめ": "#2BB1C6",
        "りんかい線": "#00A0E9",
        "山手線": "#9ACD32",
        "京浜東北線": "#00B7EE",
        "中央線": "#F15A24",
        "総武線": "#FFD400",
        "埼京線": "#00A650",
    }


# =========================================================
# 3. LOAD
# =========================================================
st = gpd.read_file(P_ST, encoding="cp932")
sec = gpd.read_file(P_SEC, encoding="cp932")
ward = gpd.read_file(P_WARD, encoding="cp932")
rid = gpd.read_file(P_RID, encoding="cp932")
raw_ju = pd.read_excel(P_JU, header=None)

print("Loaded:")
print(" st  :", len(st))
print(" sec :", len(sec))
print(" ward:", len(ward))
print(" rid :", len(rid))

if st.crs != ward.crs:
    st = st.to_crs(ward.crs)
if sec.crs != ward.crs:
    sec = sec.to_crs(ward.crs)
if rid.crs != ward.crs:
    rid = rid.to_crs(ward.crs)


# =========================================================
# 4. TOKYO23 FILTER
# =========================================================
wd = ward[ward["N03_001"].astype(str).str.strip() == "東京都"].copy()
wd23 = wd[wd["N03_004"].astype(str).isin(TOKYO23)].copy()
poly23 = wd23.union_all()

st23 = st[st.within(poly23)].copy()
sec23 = sec[sec.intersects(poly23)].copy()

st23["N05_001"] = pd.to_numeric(st23["N05_001"], errors="coerce")
sec23["N05_001"] = pd.to_numeric(sec23["N05_001"], errors="coerce")

st23 = st23[st23["N05_001"].isin(KEEP_OP)].copy()
sec23 = sec23[sec23["N05_001"].isin(KEEP_OP)].copy()

print("Tokyo23 stations:", len(st23))
print("Tokyo23 sections:", len(sec23))


# =========================================================
# 5. RAW NODES + RIDERSHIP
# =========================================================
raw = st23.copy().reset_index(drop=True)
raw["node_id"] = raw.index
raw["station_name"] = raw["N05_011"].apply(norm_station)

rid23 = rid[rid.within(poly23)].copy()
rid23["S12_005"] = pd.to_numeric(rid23["S12_005"], errors="coerce")
rid23 = rid23[rid23["S12_005"].isin(list(KEEP_OP))].copy()

raw_m = raw.to_crs("EPSG:3857").copy()
rid_m = rid23.to_crs("EPSG:3857").copy()

join = gpd.sjoin_nearest(
    rid_m,
    raw_m[["node_id", "geometry"]],
    how="left",
    distance_col="dist_m"
)

for c in Y_COLS:
    join[c] = pd.to_numeric(join[c], errors="coerce")

rid_by = join.groupby("node_id")[Y_COLS].sum(min_count=1).reset_index()
raw_m = raw_m.merge(rid_by, on="node_id", how="left")

for c in Y_COLS:
    raw_m[c] = pd.to_numeric(raw_m[c], errors="coerce").fillna(0.0)

raw_m["rid_sum"] = raw_m[Y_COLS].sum(axis=1)
raw_m = raw_m[raw_m["rid_sum"] > 0].copy().reset_index(drop=True)

print("Raw nodes with ridership:", len(raw_m))


# =========================================================
# 6. SAME NAME MERGE + DBSCAN
# =========================================================
tmp = raw_m.copy()
tmp["x"] = tmp.geometry.x
tmp["y"] = tmp.geometry.y

agg = {
    "x": "median",
    "y": "median",
    "N05_011": lambda s: list(sorted(set(map(str, s)))),
    "N05_002": lambda s: list(sorted(set(map(str, s)))),
    "N05_003": lambda s: list(sorted(set(map(str, s)))),
    "N05_001": "first",
    "rid_sum": "sum",
}
for c in Y_COLS:
    agg[c] = "sum"

nm = tmp.groupby("station_name", as_index=False).agg(agg)
nm = gpd.GeoDataFrame(nm, geometry=gpd.points_from_xy(nm["x"], nm["y"]), crs=tmp.crs)
nm = nm.to_crs("EPSG:3857").reset_index(drop=True)

xy = np.vstack([nm.geometry.x, nm.geometry.y]).T
db = DBSCAN(eps=DB_EPS, min_samples=1).fit(xy)
nm["db"] = db.labels_
nm["x"] = nm.geometry.x
nm["y"] = nm.geometry.y

def flatten_unique_lists(series):
    vals = []
    for item in series:
        if isinstance(item, list):
            vals.extend(item)
        else:
            vals.append(item)
    return sorted(set(map(str, vals)))

agg2 = {
    "x": "mean",
    "y": "mean",
    "station_name": lambda s: sorted(set(map(str, s))),
    "N05_011": flatten_unique_lists,
    "N05_002": flatten_unique_lists,
    "N05_003": flatten_unique_lists,
    "N05_001": "first",
    "rid_sum": "sum",
}
for c in Y_COLS:
    agg2[c] = "sum"

nd = nm.groupby("db", as_index=False).agg(agg2)
nd = gpd.GeoDataFrame(
    nd,
    geometry=gpd.points_from_xy(nd["x"], nd["y"]),
    crs="EPSG:3857"
).to_crs(ward.crs)

nd = nd.reset_index(drop=True)
nd["node_id"] = range(len(nd))
nd["station_repr"] = nd["station_name"].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else str(x))

print("Final nodes:", len(nd))


# =========================================================
# 7. WARD TABLE
# =========================================================
use_cols = [0, 2, 3] + list(range(4, 16))
ju = raw_ju[use_cols].copy()
ju.columns = [
    "year_raw", "pref_raw", "ward_raw",
    "night_total",
    "no_work_school",
    "work_at_home",
    "work_same_ward",
    "work_other_muni",
    "work_other_ward",
    "work_other_muni_in_pref",
    "work_other_pref",
    "day_total",
    "day_from_other_ward",
    "day_from_other_muni_in_pref",
    "day_from_other_pref"
]

ju["pref_name"] = ju["pref_raw"].apply(take_name)
ju["ward_name"] = ju["ward_raw"].apply(take_name)
ju["year"] = pd.to_numeric(ju["year_raw"].astype(str).str.replace("年", "", regex=False), errors="coerce")

num_cols = [
    "night_total","no_work_school","work_at_home","work_same_ward",
    "work_other_muni","work_other_ward","work_other_muni_in_pref","work_other_pref",
    "day_total","day_from_other_ward","day_from_other_muni_in_pref","day_from_other_pref"
]

for c in num_cols:
    ju[c] = pd.to_numeric(
        ju[c].astype(str).str.replace(",", "").str.replace("−", "-"),
        errors="coerce"
    )

ju = ju[
    (ju["pref_name"] == "東京都") &
    (ju["ward_name"].isin(TOKYO23)) &
    (ju["year"] == TARGET_YEAR)
].copy()

ju = ju.groupby("ward_name", as_index=False)[num_cols].sum(min_count=1)
ju = ju.rename(columns={"ward_name": "ward"})
ju["day_night"] = ju["day_total"] / ju["night_total"].replace(0, np.nan)
ju["net_in"] = ju["day_total"] - ju["night_total"]
ju["out_rate"] = ju["work_other_muni"] / ju["night_total"].replace(0, np.nan)
ju["in_pref_rate"] = ju["day_from_other_pref"] / ju["day_total"].replace(0, np.nan)

wd23_g = wd23.copy()
wd23_g["ward"] = wd23_g["N03_004"].astype(str).str.strip()
wd23_g = wd23_g[["ward", "geometry"]].copy()

nd = gpd.sjoin(nd, wd23_g, how="left", predicate="within").drop(columns=["index_right"], errors="ignore")
nd["ward"] = nd["ward"].astype(str).str.strip()
ju["ward"] = ju["ward"].astype(str).str.strip()

nd = nd.merge(
    ju[["ward", "day_night", "net_in", "out_rate", "in_pref_rate"]],
    on="ward",
    how="left",
    validate="m:1"
)

nd["day_night"] = pd.to_numeric(nd["day_night"], errors="coerce").fillna(1.0)
nd["net_in"] = pd.to_numeric(nd["net_in"], errors="coerce").fillna(0.0)
nd["out_rate"] = pd.to_numeric(nd["out_rate"], errors="coerce").fillna(0.0)
nd["in_pref_rate"] = pd.to_numeric(nd["in_pref_rate"], errors="coerce").fillna(0.0)


# =========================================================
# 8. BOUNDARY BLEND
# =========================================================
nd_m = nd.to_crs("EPSG:3857").copy()
wd23_m = wd23_g.to_crs("EPSG:3857").copy()
wd_poly = wd23_m.dissolve(by="ward", as_index=False)[["ward", "geometry"]].copy()

d_day = ju.set_index("ward")["day_night"].to_dict()
d_net = ju.set_index("ward")["net_in"].to_dict()
d_out = ju.set_index("ward")["out_rate"].to_dict()
d_inp = ju.set_index("ward")["in_pref_rate"].to_dict()
d_geom = wd_poly.set_index("ward")["geometry"].to_dict()

dist_lst, other_lst, ownw_lst = [], [], []
loc_day, loc_net, loc_out, loc_inp = [], [], [], []

for _, r in nd_m.iterrows():
    own = r["ward"]
    pt = r.geometry
    geom = d_geom.get(own, None)

    if geom is None:
        dist_lst.append(np.nan)
        other_lst.append(np.nan)
        ownw_lst.append(np.nan)
        loc_day.append(r["day_night"])
        loc_net.append(r["net_in"])
        loc_out.append(r["out_rate"])
        loc_inp.append(r["in_pref_rate"])
        continue

    d = pt.distance(geom.boundary)
    ow = mix_w(d, tau=TAU, wmin=W_MIN, wmax=W_MAX)
    other, _ = get_other_ward(pt, own, wd_poly)

    dist_lst.append(d)
    other_lst.append(other)
    ownw_lst.append(ow)

    loc_day.append(mix_val(d_day.get(own), d_day.get(other), ow))
    loc_net.append(mix_val(d_net.get(own), d_net.get(other), ow))
    loc_out.append(mix_val(d_out.get(own), d_out.get(other), ow))
    loc_inp.append(mix_val(d_inp.get(own), d_inp.get(other), ow))

nd["dist_bd"] = pd.Series(dist_lst, index=nd.index)
nd["other_ward"] = pd.Series(other_lst, index=nd.index)
nd["w_own"] = pd.Series(ownw_lst, index=nd.index)

nd["loc_day_night"] = pd.Series(pd.to_numeric(loc_day, errors="coerce"), index=nd.index).fillna(nd["day_night"])
nd["loc_net_in"] = pd.Series(pd.to_numeric(loc_net, errors="coerce"), index=nd.index).fillna(nd["net_in"])
nd["loc_out_rate"] = pd.Series(pd.to_numeric(loc_out, errors="coerce"), index=nd.index).fillna(nd["out_rate"])
nd["loc_in_pref_rate"] = pd.Series(pd.to_numeric(loc_inp, errors="coerce"), index=nd.index).fillna(nd["in_pref_rate"])


# =========================================================
# 9. BASE WEIGHT
# =========================================================
nd["f_in"] = (
    nd["loc_day_night"].clip(0.95, 1.90) ** 0.22
) * (
    1 + 0.45 * nd["loc_in_pref_rate"].clip(0, 0.30)
)

nd["f_out"] = (
    1 + 0.22 * nd["loc_out_rate"].clip(0, 0.25)
)


# =========================================================
# 10. GRAPH BUILD
# =========================================================
nd_m = nd.to_crs("EPSG:3857")[["node_id", "geometry"]].copy()
sec_m = sec23.to_crs("EPSG:3857").copy()

sec_m["seg_len"] = sec_m.geometry.length
sec_m = sec_m[sec_m["seg_len"] >= MIN_SEG].copy()

buf = sec_m[["geometry"]].copy()
buf["geometry"] = buf.geometry.buffer(LINE_BUF)
buf = gpd.GeoDataFrame(buf, geometry="geometry", crs=sec_m.crs)

cand = gpd.sjoin(buf, nd_m[["node_id", "geometry"]], how="left", predicate="intersects")
cand = cand.reset_index().rename(columns={"index": "sec_id"})
cand = cand[["sec_id", "node_id"]].dropna().copy()
cand["node_id"] = cand["node_id"].astype(int)

sec_geom = sec_m.geometry.to_dict()
nd_geom = nd_m.set_index("node_id").geometry.to_dict()

def proj(sec_id, node_id):
    g = sec_geom.get(sec_id, None)
    p = nd_geom.get(node_id, None)
    if g is None or p is None or g.is_empty:
        return np.nan
    if g.geom_type == "MultiLineString":
        g = max(list(g.geoms), key=lambda x: x.length)
    return float(g.project(p))

cand["proj"] = cand.apply(lambda r: proj(r["sec_id"], r["node_id"]), axis=1)
cand = cand.dropna(subset=["proj"]).copy()
cand = cand.groupby(["sec_id", "node_id"], as_index=False)["proj"].median().sort_values(["sec_id", "proj"])

edge = []
for sid, g in cand.groupby("sec_id"):
    ids = g["node_id"].tolist()
    if len(ids) < 2:
        continue
    for u, v in zip(ids[:-1], ids[1:]):
        if u != v:
            edge.append((int(u), int(v)))

edge = pd.DataFrame(edge, columns=["u", "v"]).drop_duplicates().reset_index(drop=True)

G = nx.Graph()
G.add_nodes_from(nd["node_id"].tolist())
G.add_edges_from(edge.itertuples(index=False, name=None))

deg = pd.Series(dict(G.degree()), name="deg", dtype=float)
nd = nd.merge(deg, left_on="node_id", right_index=True, how="left")
nd["deg"] = nd["deg"].fillna(0).astype(int)

print("Graph nodes:", G.number_of_nodes(), "edges:", G.number_of_edges())


# =========================================================
# 11. NETWORK FEATURES
# =========================================================
sec_line = sec23.to_crs("EPSG:3857").copy()
sec_line["line_norm"] = sec_line["N05_002"].apply(norm_line)

node_buf = nd.to_crs("EPSG:3857")[["node_id", "geometry"]].copy()
node_buf["geometry"] = node_buf.geometry.buffer(80)

lj = gpd.sjoin(
    gpd.GeoDataFrame(node_buf, geometry="geometry", crs="EPSG:3857"),
    sec_line[["line_norm", "geometry"]],
    how="left",
    predicate="intersects"
)

nline = (
    lj.dropna(subset=["line_norm"])
    .groupby("node_id")["line_norm"]
    .nunique()
    .rename("n_lines")
)

nd = nd.merge(nline, left_on="node_id", right_index=True, how="left")
nd["n_lines"] = nd["n_lines"].fillna(1).astype(int)
nd["is_transfer"] = (nd["n_lines"] >= 2).astype(int)

bet = nx.betweenness_centrality(G, normalized=True)
close = nx.closeness_centrality(G)

nd["betweenness"] = nd["node_id"].map(bet).fillna(0.0)
nd["closeness"] = nd["node_id"].map(close).fillna(0.0)

core = nx.core_number(G) if G.number_of_edges() > 0 else {nid: 0 for nid in G.nodes()}
nd["k_core"] = nd["node_id"].map(core).fillna(0).astype(int)

art = set(nx.articulation_points(G)) if G.number_of_edges() > 0 else set()
nd["art_flag"] = nd["node_id"].isin(art).astype(int)

nd["reach2"] = nd["node_id"].apply(
    lambda nid: max(len(nx.single_source_shortest_path_length(G, nid, cutoff=2)) - 1, 0)
)

m1, m2, m3 = neigh_stats(nd, G, RID_COL)
nd["nb_mean"] = m1
nd["nb_med"] = m2
nd["nb_max"] = m3

nd["rid_nb_ratio"] = (
    pd.to_numeric(nd[RID_COL], errors="coerce").fillna(0.0) /
    ((0.7 * nd["nb_med"].fillna(0.0) + 0.3 * nd["nb_max"].fillna(0.0)) + 1e-9)
)

nd["hub_exp"], hubs = hub_exposure(nd, G, RID_COL, q=HUB_Q, max_hop=MAX_HOP)


# =========================================================
# 12. DIFFUSED SIGNAL
# =========================================================
ids = nd["node_id"].tolist()
A = nx.to_numpy_array(G, nodelist=ids, dtype=float)
deg_arr = A.sum(axis=1)
deg_safe = np.where(deg_arr == 0, 1.0, deg_arr)
P = (A.T / deg_safe).T

for yr, col in Y_MAP.items():
    r = pd.to_numeric(nd[col], errors="coerce").fillna(0.0)
    x0 = (r * nd["f_in"] * nd["f_out"] * np.sqrt(nd["deg"].clip(lower=1))).values.astype(float)
    xt = x0.copy()
    for _ in range(STEPS):
        xt = ALPHA * x0 + (1.0 - ALPHA) * (P @ xt)
    nd[f"sig_{yr}"] = xt

nd["sig"] = nd["sig_2017"]
nd["sig_local_ratio"] = nd["sig"] / (nd["nb_mean"].fillna(0.0) + LOCAL_EPS)


# =========================================================
# 13. SIGNAL AXES (6D + residual) 
# =========================================================
df = nd.copy()

df["log_rid"] = np.log1p(pd.to_numeric(df[RID_COL], errors="coerce").fillna(0.0))
df["log_deg"] = np.log1p(df["deg"])
df["log_bd"] = np.log1p(pd.to_numeric(df["dist_bd"], errors="coerce").fillna(0.0))

yrs = np.array([2011, 2012, 2013, 2014, 2015, 2016, 2017], dtype=float)
df["rid_slope"] = df[Y_COLS].apply(lambda r: slope(yrs, r.values.astype(float)), axis=1)
df["rid_cv"] = df[Y_COLS].std(axis=1) / (df[Y_COLS].mean(axis=1) + 1e-9)
df["rid_stab"] = 1.0 / (df["rid_cv"] + 1e-6)

sig_cols = [f"sig_{y}" for y in range(2011, 2018)]
df["sig_growth"] = np.log1p(df["sig_2017"]) - np.log1p(df["sig_2011"])
df["sig_slope"] = df[sig_cols].apply(lambda r: slope(yrs, r.values.astype(float)), axis=1)
df["sig_cv"] = df[sig_cols].std(axis=1) / (df[sig_cols].mean(axis=1) + 1e-9)
df["sig_stab"] = 1.0 / (df["sig_cv"] + 1e-6)

df["demand"] = (
    0.56 * z(df["log_rid"]).fillna(0.0) +
    0.15 * z(np.log1p(df["rid_sum"])).fillna(0.0) +
    0.10 * z(df["rid_slope"]).fillna(0.0) +
    0.10 * z(df["rid_stab"]).fillna(0.0) +
    0.10 * z(df["sig_growth"]).fillna(0.0)
)

def signed_log1p(x):
    x = pd.to_numeric(x, errors="coerce").astype(float)
    return np.sign(x) * np.log1p(np.abs(x))

df["flow_raw"] = (
    0.35 * z(df["loc_day_night"]).fillna(0.0) +
    0.30 * z(df["loc_net_in"]).fillna(0.0) +
    0.20 * z(df["loc_in_pref_rate"]).fillna(0.0) -
    0.15 * z(df["loc_out_rate"]).fillna(0.0)
)

df["flow"] = z(signed_log1p(df["flow_raw"])).fillna(0.0)

df["transfer"] = (
    0.49 * z(df["n_lines"]).fillna(0.0) +
    0.14 * z(df["is_transfer"]).fillna(0.0) +
    0.07 * z(df["betweenness"]).fillna(0.0)
)

df["struct"] = (
    0.24 * z(df["log_deg"]).fillna(0.0) +
    0.20 * z(df["closeness"]).fillna(0.0) +
    0.16 * z(df["k_core"]).fillna(0.0) +
    0.21 * z(df["hub_exp"]).fillna(0.0) +
    0.14 * z(df["sig"]).fillna(0.0) +
    0.10 * z(df["sig_slope"]).fillna(0.0)
)

df["indep"] = (
    0.40 * z(np.log1p(df["rid_nb_ratio"].clip(lower=0.0))).fillna(0.0) -
    0.60 * z(df["hub_exp"]).fillna(0.0)
)

df["temp"] = (
    0.45 * z(df["sig_growth"]).fillna(0.0) +
    0.35 * z(df["sig_slope"]).fillna(0.0) +
    0.20 * z(df["sig_stab"]).fillna(0.0)
)

# residual
exp_feat = [
    "log_deg", "n_lines", "is_transfer", "betweenness", "closeness", "k_core",
    "loc_day_night", "loc_net_in", "loc_out_rate", "loc_in_pref_rate", "log_bd", "w_own"
]

use = df.copy()
y = pd.to_numeric(use["log_rid"], errors="coerce")
X = use[exp_feat].apply(pd.to_numeric, errors="coerce")
X = X.fillna(X.median())

rf = sm.OLS(y, sm.add_constant(X)).fit()
pred_exp = rf.predict(sm.add_constant(X))
df["resid"] = df["log_rid"] - pred_exp
df["resid"] = z_clip(df["resid"], 0.01, 0.99)

# merge back
keep = ["node_id", "demand", "flow", "transfer", "struct", "indep", "resid", "temp", "sig_growth", "sig_slope", "sig_stab", "log_rid"]
nd = nd.merge(df[keep], on="node_id", how="left")


# =========================================================
# 14. RIDERSHIP VS SIGNAL REGRESSION TEST
# =========================================================
print("\n=== Regression test: ridership vs signal ===")

reg_targets = ["betweenness", "closeness", "deg", "k_core", "hub_exp"]
reg_rows = []

for target in reg_targets:
    y = pd.to_numeric(df[target], errors="coerce")

    X1 = sm.add_constant(df["log_rid"])
    m1 = sm.OLS(y, X1, missing="drop").fit()

    X2 = sm.add_constant(df["sig"])
    m2 = sm.OLS(y, X2, missing="drop").fit()

    reg_rows.append({
        "target": target,
        "R2_ridership": m1.rsquared,
        "R2_signal": m2.rsquared,
        "Delta_signal_minus_ridership": m2.rsquared - m1.rsquared
    })

reg_df = pd.DataFrame(reg_rows)
print(reg_df.round(4).to_string(index=False))


# =========================================================
# 15. MEGA HUB FIX
# =========================================================
top_ids = set(df.sort_values(RID_COL, ascending=False).head(MEGA_N)["node_id"].tolist())
nd["is_mega"] = nd["node_id"].isin(top_ids).astype(int)


# =========================================================
# 16. FEATURE SCALE / CORR / STD / VAR
# =========================================================
feat = ["demand", "flow", "transfer", "struct", "indep", "temp"]

print("\n=== Feature std ===")
print(df[feat].std().round(4).to_string())

print("\n=== Feature variance ===")
print(df[feat].var().round(4).to_string())

scale_df = pd.DataFrame({
    "feature": feat,
    "mean": df[feat].mean().values,
    "std": df[feat].std().values,
    "var": df[feat].var().values,
    "min": df[feat].min().values,
    "max": df[feat].max().values,
})

corr = df[feat].corr()
print("\n=== Axes correlation ===")
print(corr.round(3).to_string())

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, fmt=".2f")
plt.title("Axes correlation")
plt.tight_layout()
plt.show()


# =========================================================
# 18. GMM
# =========================================================
gdf = nd.copy()
fit_df = gdf[gdf["is_mega"] == 0].copy()

X = fit_df[feat].apply(pd.to_numeric, errors="coerce").fillna(0.0)
scaler = StandardScaler()
Xz = scaler.fit_transform(X)

gmm = GaussianMixture(
    n_components=GMM_K,
    covariance_type="full",
    random_state=RAND
)
gmm.fit(Xz)

prob = gmm.predict_proba(Xz)
fit_df["cluster"] = gmm.predict(Xz)

for i in range(GMM_K):
    fit_df[f"p_{i}"] = prob[:, i]

prof = fit_df.groupby("cluster")[feat].mean().copy()
print("\n=== GMM cluster profile ===")
print(prof.round(4).to_string())


# =========================================================
# 19. CLUSTER → ROLE
# =========================================================
tmp = prof.copy()

tmp["score_cbd"] = 0.45 * tmp["flow"] + 0.35 * tmp["demand"] + 0.20 * tmp["struct"]
tmp["score_transfer"] = 0.65 * tmp["transfer"] + 0.15 * tmp["struct"] + 0.15 * tmp["demand"]
tmp["score_sub"] = (
    0.35 * tmp["indep"]
    - 0.25 * np.abs(tmp["flow"] - 0.05)
    - 0.20 * np.abs(tmp["demand"] - 0.20)
    - 0.10 * np.abs(tmp["struct"] - 0.00)
    - 0.20 * np.maximum(tmp["transfer"] - 0.20, 0)
)
tmp["score_resi"] = -0.45 * tmp["flow"] - 0.20 * tmp["transfer"] - 0.15 * tmp["struct"] + 0.20 * tmp["indep"]

roles_core = ["CBD", "Transfer Hub", "Sub-center", "Residential"]
score_cols = {
    "CBD": "score_cbd",
    "Transfer Hub": "score_transfer",
    "Sub-center": "score_sub",
    "Residential": "score_resi",
}

avail = set(tmp.index.tolist())
c2r = {}

for role in roles_core:
    s = tmp.loc[list(avail), score_cols[role]].sort_values(ascending=False)
    best = s.index[0]
    c2r[best] = role
    avail.remove(best)

for k in avail:
    scores = {r: tmp.loc[k, score_cols[r]] for r in roles_core}
    c2r[k] = max(scores, key=scores.get)

print("\n=== Cluster -> role ===")
print(c2r)

fit_df["role_raw"] = fit_df["cluster"].map(c2r)


# =========================================================
# 20. FINAL ROLE (ARGMAX)
# =========================================================

role_list = ["CBD", "Transfer Hub", "Sub-center", "Residential"]

for r in role_list:
    fit_df[f"prob_{r}"] = 0.0

for c in range(GMM_K):
    rr = c2r[c]
    fit_df[f"prob_{rr}"] += fit_df[f"p_{c}"]

fit_df["urban_role"] = fit_df[[f"prob_{r}" for r in role_list]] \
    .idxmax(axis=1) \
    .str.replace("prob_", "", regex=False)

fit_df["prob_max"] = fit_df[[f"prob_{r}" for r in role_list]].max(axis=1)

mega = gdf[gdf["is_mega"] == 1].copy()
mega["cluster"] = -1
mega["urban_role"] = "Mega Hub"

for r in role_list:
    mega[f"prob_{r}"] = 0.0

mega["prob_max"] = 1.0

final = pd.concat([fit_df, mega], ignore_index=True)

print("\n=== Final role counts ===")
print(final["urban_role"].value_counts().to_string())


# =========================================================
# 21. PLOT PREP
# =========================================================
lc = get_line_colors()
rc = get_role_colors()

sec_plot = sec23.to_crs(wd23.crs).copy()
sec_plot["line_norm"] = sec_plot["N05_002"].apply(norm_line)
line_names = sorted(sec_plot["line_norm"].dropna().unique())

plot_df = final.to_crs(wd23.crs).copy()
plot_df[RID_COL] = pd.to_numeric(plot_df[RID_COL], errors="coerce").fillna(0.0)

u23 = wd23.union_all()
plot_df = plot_df[plot_df.intersects(u23.buffer(1e-9))].copy()

mask = plot_df[RID_COL] > 0
sizes = mk_sizes(plot_df[RID_COL], smin=20, smax=350, mode="sqrt")

th = 300_000
mb = plot_df[RID_COL] > th
vals = plot_df.loc[mb, RID_COL].astype(float)
if len(vals) > 0:
    zz = (vals - th) / (vals.max() - th + 1e-9)
    sizes.loc[mb] = sizes.loc[mb] * (1 + 1.4 * zz)

plot_df["plot_size"] = sizes

minx, miny, maxx, maxy = wd23.total_bounds
padx = (maxx - minx) * 0.03
pady = (maxy - miny) * 0.03


# =========================================================
# 22. MAIN ROLE MAP
# =========================================================
fig, ax = plt.subplots(figsize=(12, 12))
wd23.plot(ax=ax, color="#efefef", edgecolor="#b0b0b0", zorder=1)

for ln in line_names:
    sg = sec_plot[sec_plot["line_norm"] == ln]
    sg.plot(
        ax=ax,
        linewidth=1.2 if ln in lc else 0.8,
        color=lc.get(ln, "#b8c4d6"),
        alpha=0.85 if ln in lc else 0.55,
        zorder=2
    )

order = ["Residential", "Sub-center", "Transfer Hub", "CBD", "Mega Hub"]

for rr in order:
    g = plot_df[(plot_df["urban_role"] == rr) & mask].copy()
    if len(g) == 0:
        continue
    ax.scatter(
        g.geometry.x, g.geometry.y,
        s=g["plot_size"],
        c=rc.get(rr, "gray"),
        edgecolors="white",
        linewidths=0.4,
        alpha=0.72,
        zorder=3 if rr != "Mega Hub" else 4
    )

handles = []
for rr in order:
    n = ((plot_df["urban_role"] == rr) & mask).sum()
    if n == 0:
        continue
    handles.append(
        Line2D([0], [0], marker='o', color='w',
               label=f"{rr} ({n})",
               markerfacecolor=rc.get(rr, "gray"),
               markeredgecolor="white", markeredgewidth=0.8,
               markersize=8, linewidth=0)
    )

ax.legend(handles=handles, loc="lower left", frameon=True, title="Role")
ax.set_xlim(minx - padx, maxx + padx)
ax.set_ylim(miny - pady, maxy + pady)
ax.set_axis_off()
plt.tight_layout()
plt.show()


# =========================================================
# 23. FUNCTION PROBABILITY MAPS
# =========================================================
base_plot = final.to_crs(wd23.crs).copy()
base_plot[RID_COL] = pd.to_numeric(base_plot[RID_COL], errors="coerce").fillna(0.0)

u23 = wd23.union_all()
base_plot = base_plot[base_plot.intersects(u23.buffer(1e-9))].copy()

mask = base_plot[RID_COL] > 0

# point size
sizes = mk_sizes(base_plot[RID_COL], smin=20, smax=350, mode="sqrt")

th = 300_000
mb = base_plot[RID_COL] > th
vals = base_plot.loc[mb, RID_COL].astype(float)
if len(vals) > 0:
    zz = (vals - th) / (vals.max() - th + 1e-9)
    sizes.loc[mb] = sizes.loc[mb] * (1 + 1.4 * zz)

base_plot["plot_size"] = sizes

# probability difference
base_plot["cbd_vs_resi"] = (
    pd.to_numeric(base_plot["prob_CBD"], errors="coerce").fillna(0.0) -
    pd.to_numeric(base_plot["prob_Residential"], errors="coerce").fillna(0.0)
)

base_plot["transfer_vs_sub"] = (
    pd.to_numeric(base_plot["prob_Transfer Hub"], errors="coerce").fillna(0.0) -
    pd.to_numeric(base_plot["prob_Sub-center"], errors="coerce").fillna(0.0)
)

diff_maps = [
    ("cbd_vs_resi", "CBD  ↔  Residential", "coolwarm"),
    ("transfer_vs_sub", "Transfer Hub  ↔  Sub-center", "coolwarm"),
]

fig, axes = plt.subplots(1, 2, figsize=(16, 8))
axes = axes.flatten()

for ax, (col, ttl, cmap) in zip(axes, diff_maps):
    wd23.plot(ax=ax, color="#efefef", edgecolor="#b0b0b0", zorder=1)

    for ln in line_names:
        sg = sec_plot[sec_plot["line_norm"] == ln]
        sg.plot(
            ax=ax,
            linewidth=0.9 if ln in lc else 0.6,
            color=lc.get(ln, "#b8c4d6"),
            alpha=0.45 if ln in lc else 0.25,
            zorder=2
        )

    vals = pd.to_numeric(base_plot[col], errors="coerce")
    vmax = np.nanpercentile(np.abs(vals), 98)
    vmax = max(vmax, 1e-6)

    sc = ax.scatter(
        base_plot.loc[mask, "geometry"].x,
        base_plot.loc[mask, "geometry"].y,
        c=base_plot.loc[mask, col],
        s=base_plot.loc[mask, "plot_size"] * 0.30,
        cmap=cmap,
        vmin=-vmax,
        vmax=vmax,
        edgecolors="black",
        linewidths=0.20,
        alpha=0.75,
        zorder=3
    )

    cb = plt.colorbar(sc, ax=ax, fraction=0.035, pad=0.01)
    cb.set_label(ttl)

    ax.set_title(ttl)
    ax.set_xlim(minx - padx, maxx + padx)
    ax.set_ylim(miny - pady, maxy + pady)
    ax.set_axis_off()

plt.tight_layout()
plt.show()


# =========================================================
# 24. PCA
# =========================================================
pca_feat = feat.copy()
Xp = final[pca_feat].apply(pd.to_numeric, errors="coerce").fillna(0.0)

sc_pca = StandardScaler()
Xp_z = sc_pca.fit_transform(Xp)

pca = PCA(n_components=3, random_state=RAND)
pc = pca.fit_transform(Xp_z)

pca_df = final.copy()
pca_df["PC1"] = pc[:, 0]
pca_df["PC2"] = pc[:, 1]
pca_df["PC3"] = pc[:, 2]

print("\n=== PCA explained variance ===")
for i, v in enumerate(pca.explained_variance_ratio_, start=1):
    print(f"PC{i}: {v:.4f}")
print("Total:", pca.explained_variance_ratio_.sum().round(4))

load = pd.DataFrame(
    pca.components_.T,
    index=pca_feat,
    columns=["PC1", "PC2", "PC3"]
)
print("\n=== PCA loadings ===")
print(load.round(4).to_string())


# =========================================================
# 25. PCA SCATTER WITH EXPLANATION
# =========================================================
fig, ax = plt.subplots(figsize=(9, 8))

for rr in order:
    g = pca_df[pca_df["urban_role"] == rr].copy()
    if len(g) == 0:
        continue
    ax.scatter(
        g["PC1"], g["PC2"],
        s=28,
        c=rc.get(rr, "#888888"),
        alpha=0.72,
        edgecolors="white",
        linewidths=0.35
    )

handles = []
for rr in order:
    n = (pca_df["urban_role"] == rr).sum()
    if n == 0:
        continue
    handles.append(
        Line2D([0], [0], marker='o', color='w',
               label=f"{rr} ({n})",
               markerfacecolor=rc.get(rr, "#888888"),
               markeredgecolor="white", markeredgewidth=0.8,
               markersize=8, linewidth=0)
    )

ax.axhline(0, color="#cccccc", linewidth=0.8)
ax.axvline(0, color="#cccccc", linewidth=0.8)

ax.set_title("PCA space (Roles)")
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)  |  Centrality")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)  |  Independence")

ax.annotate("Central →", xy=(0.80, -0.08), xycoords="axes fraction", fontsize=10)
ax.annotate("← Peripheral", xy=(0.03, -0.08), xycoords="axes fraction", fontsize=10)

ax.annotate("Independent ↑", xy=(-0.08, 0.82), xycoords="axes fraction", fontsize=10, rotation=90)
ax.annotate("↓ Dependent", xy=(-0.08, 0.08), xycoords="axes fraction", fontsize=10, rotation=90)

x1 = np.nanpercentile(pca_df["PC1"], 70)
x2 = np.nanpercentile(pca_df["PC1"], 30)
y1 = np.nanpercentile(pca_df["PC2"], 70)
y2 = np.nanpercentile(pca_df["PC2"], 30)

ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True, title="Role")
plt.tight_layout()
plt.show()

# =========================================================
# 26. AXES MAP
# =========================================================
axis_maps = [
    ("demand", "Demand", "Reds"),
    ("flow", "Flow", "Blues"),
    ("transfer", "Transfer", "Oranges"),
    ("struct", "Struct", "Purples"),
    ("indep", "Independence", "Greens"),
    ("temp", "Temporal", "Greys"),
]

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

base_plot = final.to_crs(wd23.crs).copy()
base_plot[RID_COL] = pd.to_numeric(base_plot[RID_COL], errors="coerce").fillna(0.0)

u23 = wd23.union_all()
base_plot = base_plot[base_plot.intersects(u23.buffer(1e-9))].copy()

mask = base_plot[RID_COL] > 0

sizes = mk_sizes(base_plot[RID_COL], smin=20, smax=350, mode="sqrt")

th = 300_000
mb = base_plot[RID_COL] > th
vals = base_plot.loc[mb, RID_COL].astype(float)

if len(vals) > 0:
    zz = (vals - th) / (vals.max() - th + 1e-9)
    sizes.loc[mb] = sizes.loc[mb] * (1 + 1.4 * zz)

base_plot["plot_size"] = sizes

for ax, (col, ttl, cmap) in zip(axes, axis_maps):
    wd23.plot(ax=ax, color="#efefef", edgecolor="#b0b0b0", zorder=1)

    for ln in line_names:
        sg = sec_plot[sec_plot["line_norm"] == ln]
        sg.plot(
            ax=ax,
            linewidth=0.9 if ln in lc else 0.6,
            color=lc.get(ln, "#b8c4d6"),
            alpha=0.45 if ln in lc else 0.25,
            zorder=2
        )

    vals = pd.to_numeric(base_plot[col], errors="coerce")
    vmax = np.nanpercentile(np.abs(vals), 98)
    vmax = max(vmax, 1e-6)

    sc = ax.scatter(
        base_plot.loc[mask, "geometry"].x,
        base_plot.loc[mask, "geometry"].y,
        c=base_plot.loc[mask, col],
        s=base_plot.loc[mask, "plot_size"] * 0.30,
        cmap=cmap,
        vmin=-vmax,
        vmax=vmax,
        edgecolors="black",
        linewidths=0.20,
        alpha=0.75,
        zorder=3
    )

    cb = plt.colorbar(sc, ax=ax, fraction=0.035, pad=0.01)
    cb.set_label(ttl)

    ax.set_title(ttl)
    ax.set_xlim(minx - padx, maxx + padx)
    ax.set_ylim(miny - pady, maxy + pady)
    ax.set_axis_off()

plt.tight_layout()
plt.show()


# =========================================================
# 27. ENTROPY MAP
# =========================================================
prob_cols = [
    "prob_CBD",
    "prob_Transfer Hub",
    "prob_Sub-center",
    "prob_Residential"
]

P = final[prob_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).values
final["entropy"] = -np.sum(P * np.log(P + 1e-9), axis=1)

base_plot = final.to_crs(wd23.crs).copy()
base_plot[RID_COL] = pd.to_numeric(base_plot[RID_COL], errors="coerce").fillna(0.0)

u23 = wd23.union_all()
base_plot = base_plot[base_plot.intersects(u23.buffer(1e-9))].copy()

mask = base_plot[RID_COL] > 0

sizes = mk_sizes(base_plot[RID_COL], smin=20, smax=350, mode="sqrt")

th = 300_000
mb = base_plot[RID_COL] > th
vals = base_plot.loc[mb, RID_COL].astype(float)
if len(vals) > 0:
    zz = (vals - th) / (vals.max() - th + 1e-9)
    sizes.loc[mb] = sizes.loc[mb] * (1 + 1.4 * zz)

base_plot["plot_size"] = sizes

fig, ax = plt.subplots(figsize=(12, 12))
wd23.plot(ax=ax, color="#efefef", edgecolor="#b0b0b0", zorder=1)

for ln in line_names:
    sg = sec_plot[sec_plot["line_norm"] == ln]
    sg.plot(
        ax=ax,
        linewidth=1.0 if ln in lc else 0.7,
        color=lc.get(ln, "#b8c4d6"),
        alpha=0.60 if ln in lc else 0.40,
        zorder=2
    )

sc = ax.scatter(
    base_plot.loc[mask, "geometry"].x,
    base_plot.loc[mask, "geometry"].y,
    c=base_plot.loc[mask, "entropy"],
    s=base_plot.loc[mask, "plot_size"] * 0.40,
    cmap="viridis",
    edgecolors="black",
    linewidths=0.20,
    alpha=0.75,
    zorder=3
)

cb = plt.colorbar(sc, ax=ax, fraction=0.035, pad=0.01)
cb.set_label("Functional mixing (entropy)")

ax.set_title("Functional Mixing Map")
ax.set_xlim(minx - padx, maxx + padx)
ax.set_ylim(miny - pady, maxy + pady)
ax.set_axis_off()

plt.tight_layout()
plt.show()

for role in ["Transfer Hub", "Sub-center"]:
    print(f"\n=== {role} ===")
    print(
        final.loc[final["urban_role"] == role, "station_name"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .to_string(index=False)
    )