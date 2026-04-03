# Tokyo Railway Network Analysis

![](outputs/Role_Map.png)

A data science project that classifies **station roles in Tokyo’s 23 wards beyond ridership alone**.

This project asks a simple question:

**Can station importance be understood only by passenger volume?**

To answer this, I built a structure-aware analytical framework that integrates:

- railway network structure
- ridership
- urban flow context
- diffusion-based signals
- unsupervised role classification

---

## Overview

In large metropolitan railway systems such as Tokyo, station importance is often measured by ridership.  
However, passenger volume alone does not fully explain:

- structural importance in the network
- differences between transfer-oriented and business-oriented stations
- functional variation across urban space

This project addresses that limitation by combining **graph analysis, spatial context, and interpretable feature design** to classify station roles across Tokyo’s 23 wards.

---

## Key Results

- Built an integrated railway graph with **486 nodes** and **670 edges**
- Constructed a **6-dimensional feature space** for role analysis
- Confirmed that the **diffused signal outperformed ridership on most tested structural metrics**
- Identified interpretable station roles:
  - **CBD**
  - **Transfer Hub**
  - **Sub-center**
  - **Residential**
  - **Mega Hub**

---

## Why This Project Matters

Ridership mainly reflects scale.  
But in a real urban railway system, station function is also shaped by:

- connectivity
- transfer structure
- neighborhood influence
- surrounding urban context

This project shows that stations are better interpreted not as a single ranked list, but as nodes with different **structural and functional roles**.

More broadly, this project demonstrates how urban data science can move beyond simple size-based ranking through **problem redefinition, feature design, validation, and interpretation**.

---

## My Contribution

This is an individual project in which I handled the full end-to-end workflow:

- defined the research question and analytical framework
- cleaned and integrated raw railway and spatial datasets
- constructed graph-based, flow-based, and signal-based features
- redesigned the representation after identifying limitations in the initial single-signal approach
- validated the framework through regression comparison and PCA
- interpreted clustering results and mapped them into functional station roles
- visualized the results for metropolitan-scale analysis

---

## Methodology

### 1. Station Integration

To construct a usable railway network, station records were cleaned and integrated through:

- station name normalization
- DBSCAN clustering (50m) for nearby station merging

Final network:

- **486 nodes**
- **670 edges**

---

### 2. Feature Construction

Each station was represented from multiple perspectives.

#### Network structure features
- degree
- number of connected lines (`n_lines`)
- transfer indicator (`is_transfer`)
- betweenness / closeness centrality
- k-core
- two-hop reachability (`reach2`)
- neighbor ridership statistics
- relative local scale (`rid_nb_ratio`)
- hub exposure

#### Demand and urban flow features
- ridership
- day/night population ratio
- net inflow
- inter-municipality outflow rate
- inter-prefecture inflow rate

To better reflect stations near administrative boundaries, flow-related variables were adjusted using boundary-based blending with neighboring wards.

---

### 3. Diffused Signal

A station-level signal was constructed by combining ridership, urban flow indicators, and network-structure features.

The base signal was then propagated over the railway graph so that each station reflects not only its own characteristics, but also the influence of nearby stations.

    x(t+1) = α·x₀ + (1−α)·P·x_t

where:

- `P` is the transition matrix derived from graph connectivity
- `α` controls how much of the original signal is preserved

This allows the representation to capture both **local neighborhood effects** and **global structural influence**.

---

### 4. From a Single Signal to a Multi-Axis Representation

The initial approach used a single signal to represent station importance.

#### Limitation
- role separation was unclear
- large hubs strongly influenced surrounding stations
- the signal reflected scale, but not enough functional distinction

#### Improvement
To improve interpretability, the signal was decomposed into multiple axes:

- initially **7 axes**
- the **residual axis was excluded**
- the final model used a **6-dimensional feature space**

This redesign was a key step in the project, shifting the analysis from a single importance score to a more interpretable representation of station roles.

---

### 5. Final Feature Axes

The final model uses the following six axes:

- **Flow**: local inflow/outflow structure
- **Demand**: ridership scale and trend
- **Structure**: network topology and structural importance
- **Transfer**: interchange functionality
- **Independence**: relative separation from major hubs
- **Temporal**: temporal change pattern of station signal

#### Feature Correlation

![Feature Correlation](outputs/Feature_Correlation.png)

The axes are related but not fully redundant.  
In particular, **independence** shows an opposite tendency from more centrality-oriented axes, supporting its role as a complementary dimension.

#### Axis Maps

![Axes Map](outputs/Axes_Map.png)

These maps highlight different spatial dimensions of the Tokyo railway system.

---

### 6. Regression Validation

To test whether the proposed signal captures railway structure better than simple passenger volume, regression tests were conducted using:

- **Ridership**
- **Diffused signal**

#### Targets
- betweenness
- closeness
- degree
- k-core
- hub exposure

#### Results

| Metric       | Ridership | Signal | Δ |
|-------------|----------:|-------:|---:|
| betweenness | 0.1489    | 0.2422 | +0.0933 |
| closeness   | 0.1148    | 0.1274 | +0.0126 |
| degree      | 0.2245    | 0.2067 | -0.0177 |
| k-core      | 0.0335    | 0.0428 | +0.0093 |
| hub_exp     | 0.1594    | 0.1743 | +0.0149 |

Overall, the diffused signal explains network-related structure better than ridership on most evaluated metrics.

This suggests that **station importance in an urban railway system cannot be sufficiently understood through demand alone**.

---

### 7. PCA Validation

The 6D feature space is reasonably preserved, with **PC1–PC3 explaining about 80% of the variance**.

![PCA Space](outputs/PCA_Space.png)

This suggests that the feature space is structured and interpretable rather than excessively redundant.

---

### 8. GMM Clustering and Role Assignment

Stations were clustered in the 6D feature space using a **Gaussian Mixture Model (GMM, K = 5)**.

Rather than directly interpreting clusters as labels, each cluster was mapped using **role-specific scoring rules** based on feature profiles.

#### Role profiles
- **CBD**
  - high flow
  - high demand
  - high structure

- **Transfer Hub**
  - high transfer
  - high connectivity

- **Sub-center**
  - moderate values with higher independence

- **Residential**
  - low flow
  - low structure
  - higher independence

To prevent the largest stations from dominating the interpretation of all other roles, the **top 12 stations were treated separately as Mega Hubs**.

#### Role Map

![Role Map](outputs/Role_Map.png)

#### Score Map

![Score Map](outputs/Score_Map.png)

#### Functional Mixing (Entropy)

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

## Key Insights

- Ridership alone does not fully capture structural importance in urban railway networks.
- Station roles are better understood through multiple dimensions than through a single scale of importance.
- Diffused signals reveal hidden structural influence by incorporating neighborhood and network effects.
- Functional roles emerge from the interaction of **demand, flow, and structure**.
- Urban space is better interpreted as a **continuous functional gradient** than as a fixed set of discrete categories.

---

## Data

**Source:** National Land Numerical Information (MLIT Japan)

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

## Tech Stack

- Python
- pandas / geopandas
- NetworkX
- scikit-learn
- DBSCAN
- PCA
- Gaussian Mixture Model (GMM)

---

## Repository Structure

```bash
.
├── data/                # raw / processed datasets
├── outputs/             # maps and figures used in README
├── notebooks/ or src/   # analysis scripts or notebooks
└── README.md