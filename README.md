# Tokyo Railway Network Analysis

![Role Map](outputs/Role_Map.png)

A data science project that classifies **station roles in Tokyo’s 23 wards beyond ridership alone**.

## At a Glance

**Question**  
Can station importance be understood only by passenger volume?

**Approach**  
I built a structure-aware framework that combines:

- railway network structure
- ridership
- urban flow context
- diffusion-based signals
- unsupervised role classification

**Result**  
The proposed signal explained network-related structure better than ridership on most evaluated metrics, and stations could be interpreted through multiple functional roles rather than a single size-based ranking.

**What this project demonstrates**
- problem redefinition
- feature design
- graph and spatial data integration
- validation and interpretation

---

## Why This Project

In large metropolitan railway systems such as Tokyo, station importance is often measured by ridership.  
However, ridership mainly reflects scale and does not fully explain:

- structural importance in the network
- transfer-oriented vs. business-oriented roles
- functional variation across urban space

This project addresses that limitation by modeling stations as nodes with different **structural and functional roles**, rather than as points on a single ranked list.

---

## Key Results

- Built an integrated railway graph with **486 nodes** and **670 edges**
- Constructed a **6-dimensional feature space** for role analysis
- Confirmed that the **diffused signal outperformed ridership on most tested structural metrics**
- Identified interpretable station roles:
  - **CBD (Central Business District)**
  - **Transfer Hub**
  - **Sub-center**
  - **Residential**
  - **Mega Hub**

---

## My Contribution

This is an individual end-to-end project. I handled:

- research question design
- raw data cleaning and integration
- graph / flow / signal feature construction
- representation redesign from a single signal to multi-axis features
- validation through regression comparison and PCA
- clustering interpretation and role assignment
- visualization of metropolitan-scale results

---

## Method

### 1. Data Integration

Datasets used:

- Station data (`N05`)
- Railway sections (`N05`)
- Administrative boundaries (`N03`)
- Ridership (`S12`)
- Population flow (`ju01`)

To construct a usable railway network, station records were integrated through:

- station name normalization
- DBSCAN clustering (50m) for nearby station merging

Final graph:

- **486 nodes**
- **670 edges**

---

### 2. Feature Design

Each station was represented from multiple perspectives.

**Network structure features**
- degree
- number of connected lines (`n_lines`)
- transfer indicator (`is_transfer`)
- betweenness / closeness
- k-core
- two-hop reachability (`reach2`)
- neighbor ridership statistics
- relative local scale (`rid_nb_ratio`)
- hub exposure

**Demand and urban flow features**
- ridership
- day/night population ratio
- net inflow
- inter-municipality outflow rate
- inter-prefecture inflow rate

To better reflect stations near administrative boundaries, flow-related variables were adjusted using boundary-based blending with neighboring wards.

---

### 3. Diffused Signal

A station-level signal was constructed by combining ridership, urban flow indicators, and network-related features.

The base signal was then propagated over the graph:

`x(t+1) = α·x₀ + (1−α)·P·x_t`

where:

- `P` is the transition matrix from graph connectivity
- `α` controls how much of the original signal is preserved

This allows each station to reflect not only its own characteristics, but also the influence of nearby stations and broader network structure.

---

### 4. From Single Signal to Multi-Axis Representation

The initial approach used a single signal to represent station importance.

However, this had clear limitations:

- role separation was weak
- large hubs strongly influenced surrounding stations
- the signal captured scale better than function

To improve interpretability, I decomposed the representation into multiple axes.

- initial design: **7 axes**
- final design: **6 axes**
- the residual axis was removed because it was highly correlated with demand and added redundancy

This redesign was the key turning point of the project.

---

## Final Feature Axes

The final model uses the following six axes:

- **Flow**: local inflow/outflow structure
- **Demand**: ridership scale and trend
- **Structure**: network topology and structural importance
- **Transfer**: interchange functionality
- **Independence**: relative separation from major hubs
- **Temporal**: temporal change pattern of station signal

### Feature Correlation

![Feature Correlation](outputs/Feature_Correlation.png)

The axes are related but not fully redundant.  
In particular, **independence** tends to move in the opposite direction from more centrality-oriented axes, which supports its role as a complementary dimension.

### Axis Maps

![Axes Map](outputs/Axes_Map.png)

These maps show that different axes capture different spatial characteristics of Tokyo’s railway system.

---

## Validation

### 1. Regression Comparison: Ridership vs. Diffused Signal

To test whether the proposed signal captured railway structure better than passenger volume, I compared:

- **Ridership**
- **Diffused signal**

against:

- betweenness
- closeness
- degree
- k-core
- hub exposure

| Metric       | Ridership | Signal | Δ |
|-------------|----------:|-------:|---:|
| betweenness | 0.1489    | 0.2422 | +0.0933 |
| closeness   | 0.1148    | 0.1274 | +0.0126 |
| degree      | 0.2245    | 0.2067 | -0.0177 |
| k-core      | 0.0335    | 0.0428 | +0.0093 |
| hub_exp     | 0.1594    | 0.1743 | +0.0149 |

Overall, the diffused signal performed better on most structural metrics.  
While ridership remained slightly stronger for **degree**, the proposed signal showed broader explanatory power across multiple network-related indicators.

---

### 2. PCA Validation

The 6D feature space is reasonably preserved, with **PC1–PC3 explaining about 80% of the variance**.

![PCA Space](outputs/PCA_Space.png)

This suggests that the feature space is structured and interpretable rather than excessively redundant.

---

## Clustering and Role Assignment

Stations were clustered in the 6D feature space using a **Gaussian Mixture Model (GMM, K = 5)**.

Rather than directly treating clusters as labels, I mapped them into interpretable roles using feature-based scoring rules.

**Role profiles**
- **CBD**: high flow, high demand, high structure
- **Transfer Hub**: high transfer, high connectivity
- **Sub-center**: moderate overall values with higher independence
- **Residential**: low flow, low structure, relatively higher independence

To prevent the largest stations from dominating the interpretation of all other roles, the **top 12 stations were treated separately as Mega Hubs**.

### Role Map

![Role Map](outputs/Role_Map.png)

### Score Map

![Score Map](outputs/Score_Map.png)

### Entropy Map

![Entropy Map](outputs/Entropy_Map.png)

Higher entropy indicates more mixed role characteristics.

---

## Role Distribution

- **Residential:** 279
- **CBD:** 110
- **Transfer Hub:** 62
- **Sub-center:** 23
- **Mega Hub:** 12

---

## Main Insights

- Ridership alone does not fully capture structural importance in urban railway networks.
- Station roles are better understood through multiple dimensions than through a single importance score.
- Diffused signals help reveal hidden structural influence by incorporating neighborhood and network effects.
- Functional station roles emerge from the interaction of **demand, flow, and structure**.

---

## Tech Stack

- Python
- pandas / geopandas
- NetworkX
- scikit-learn
- DBSCAN
- PCA
- Gaussian Mixture Model (GMM)

---

## Data Source

**National Land Numerical Information (MLIT Japan)**

- Station data (`N05`)
- Railway sections (`N05`)
- Administrative boundaries (`N03`)
- Ridership (`S12`)
- Population flow (`ju01`)

Additional settings:
- **Ridership period:** 2011–2017
- **Reference year:** 2017
- **Temporal features:** derived from multi-year trends

Download: http://nlftp.mlit.go.jp/ksj/

---

## Limitations

- some feature axes are manually defined
- some correlation remains between axes
- results are sensitive to hyperparameter choices
- classification of smaller stations remains limited