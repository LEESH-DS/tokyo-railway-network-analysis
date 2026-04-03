# Tokyo Railway Network Analysis

![](outputs/Role_Map.png)

A data science project that classifies **station roles in Tokyo’s 23 wards beyond ridership alone**.

## Project Overview

This project analyzes station roles in Tokyo’s 23 wards using a single Python workflow that covers data integration, graph construction, feature design, signal diffusion, validation, and visualization.

It starts from a simple question:

**Can station importance be understood only by passenger volume?**

In large metropolitan railway systems such as Tokyo, ridership is often used as the main indicator of station importance.  
However, ridership mainly reflects scale and does not fully explain:

- structural importance in the railway network
- transfer-oriented vs. business-oriented functions
- functional variation across urban space

To address this, I combined:

- railway network structure
- ridership
- urban flow context
- diffusion-based signals
- unsupervised role classification

Rather than treating stations as a single ranked list, this project interprets them as nodes with different **structural and functional roles**.
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

### 3. Diffused Signal

A station-level signal was constructed by combining ridership, urban flow indicators, and network-related features.

The base signal was then propagated over the graph:

`x(t+1) = α·x₀ + (1−α)·P·x_t`

This allows each station to reflect not only its own characteristics, but also the influence of nearby stations and broader network structure.

### 4. Multi-Axis Representation

The initial approach used a single signal to represent station importance.  
However, this had limitations:

- role separation was weak
- large hubs strongly influenced nearby stations
- the signal captured scale better than function

To improve interpretability, I decomposed the representation into multiple axes.

- initial design: **7 axes**
- final design: **6 axes**
- the residual axis was removed because it was highly correlated with demand and added redundancy

The final model uses the following six axes:

- **Flow**
- **Demand**
- **Structure**
- **Transfer**
- **Independence**
- **Temporal**

---

## Validation

### Regression Comparison: Ridership vs. Diffused Signal

To test whether the proposed signal captured railway structure better than passenger volume, I compared ridership and the diffused signal against several structural targets.

| Metric       | Ridership | Signal | Δ |
|-------------|----------:|-------:|---:|
| betweenness | 0.1489    | 0.2422 | +0.0933 |
| closeness   | 0.1148    | 0.1274 | +0.0126 |
| degree      | 0.2245    | 0.2067 | -0.0177 |
| k-core      | 0.0335    | 0.0428 | +0.0093 |
| hub_exp     | 0.1594    | 0.1743 | +0.0149 |

Overall, the diffused signal performed better on most structural metrics, suggesting that station importance cannot be sufficiently understood through demand alone.

### PCA Validation

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

### Entropy Map

![Entropy Map](outputs/Entropy_Map.png)

Higher entropy indicates more mixed role characteristics.

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

