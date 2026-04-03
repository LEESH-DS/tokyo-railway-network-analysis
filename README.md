# Tokyo Railway Network Analysis

A graph-based urban analytics project that identifies **station roles in Tokyo’s 23 wards beyond ridership alone**.

Instead of evaluating stations only by passenger volume, this project combines **ridership, urban flow, network structure, and diffusion-based signals** to reveal hidden functional roles across the railway network.

---

## Overview

In large metropolitan systems like Tokyo, ridership is often treated as the main indicator of station importance.  
However, passenger volume alone cannot fully explain:

- structural position in the network
- interaction with neighboring stations
- functional differences across urban space

This project addresses that limitation by building a **structure-aware signal framework** that incorporates both **network effects** and **spatial context**.

---

## Key Results

- Built an integrated railway graph with **486 nodes** and **670 edges**
- Constructed a **6-dimensional feature space** for station role analysis
- Found that the **diffused signal outperformed ridership on most tested structural metrics**
- Identified interpretable station roles across Tokyo’s railway network:
  - **CBD (Central Business District)**
  - **Transfer Hub**
  - **Sub-center**
  - **Residential**
  - **Mega Hub**

---

## Why It Matters

This approach helps:

- identify structurally important stations that ridership alone may overlook
- understand urban functional zones beyond administrative boundaries
- support data-driven transportation and urban planning

More broadly, the project shows that **station importance is shaped not only by demand, but also by connectivity, neighborhood influence, and structural position in the network**.

---

## What This Project Shows

This repository demonstrates how to:

- integrate spatial railway data into a graph-based station network
- construct diffusion-based structural signals
- decompose station characteristics into multiple interpretable axes
- classify urban station roles using unsupervised learning

---

## Methodology

### 1. Station Integration

To construct a usable railway network, station records were cleaned and integrated through:

- station name normalization
- DBSCAN clustering (50m) to merge nearby stations

Final network:

- **486 nodes**
- **670 edges**

---

### 2. Network Feature Construction

To represent structural properties of stations, the following graph-based features were constructed:

- **n_lines**: number of railway lines connected to each station
- **is_transfer**: indicator of transfer stations (2 or more lines)
- **betweenness / closeness centrality**: network importance and accessibility
- **k-core**: embeddedness in the network core
- **reach2**: number of stations reachable within two hops
- **neighbor ridership statistics**: mean / median / max ridership of adjacent stations
- **rid_nb_ratio**: relative scale compared to neighboring stations
- **hub exposure**: influence received from major hub stations across the network

These features were combined with demand and flow signals to capture stations from multiple structural perspectives.

---

### 3. Diffused Signal

A station-level signal is constructed by combining:

- **Ridership (S12 data)**
- **Urban flow indicators**
  - day/night population ratio
  - inter-prefecture inflow rate
  - inter-municipality outflow rate
- **Network structure**
  - degree
  - centrality measures
  - number of lines

These components are normalized and combined into a base signal.

The signal is then propagated through the network so that each station reflects not only its own characteristics, but also the influence of nearby stations.

This process is modeled as:

    x(t+1) = α·x₀ + (1−α)·P·x_t

where:

- `P` is the transition matrix derived from graph connectivity
- `α` controls how much of the original signal is preserved

This allows the signal to capture both **local neighborhood effects** and **global structural influence**.

---

### 4. Signal Decomposition

The initial approach used a single signal.

#### Limitation

- role separation was unclear
- large hubs strongly influenced surrounding stations (**hub dominance effect**)

#### Solution

To improve interpretability, the signal was decomposed into multiple axes:

- initially decomposed into **7 axes**
- the **residual axis was excluded**
- the final representation became a **6-dimensional feature space**

---

### 5. Feature Axes

The final model uses a **6-dimensional feature space**, excluding the residual axis.

#### Why the residual axis was removed

- it showed high correlation with demand
- it mainly captured scale effects rather than structure
- it introduced redundancy and distortion

#### Final axes

- **Flow**: local inflow/outflow structure
- **Demand**: ridership scale and trend
- **Structure**: network topology and structural importance
- **Transfer**: interchange functionality
- **Independence**: relative separation from major hubs
- **Temporal**: temporal change pattern of station signal

#### Feature Correlation

![Feature Correlation](outputs/Feature_Correlation.png)

The axes are related but not fully redundant.  
In particular, **independence** tends to show an opposite pattern from the more centrality-oriented axes.

#### Axis Maps

![Axes Map](outputs/Axes_Map.png)

These maps highlight different spatial dimensions of the Tokyo railway system.

---

### 6. Regression Validation

Regression tests were conducted to compare:

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

Overall, the diffused signal explains network structure better than ridership on most evaluated metrics.

---

### 7. PCA Validation

The 6D feature space is well preserved, with **PC1–PC3 explaining about 80% of the variance**.

#### PCA Space

![PCA Space](outputs/PCA_Space.png)

This projection suggests that the feature space is structured and interpretable rather than excessively redundant.

---

### 8. GMM Clustering and Role Assignment

Stations were first clustered in the 6D feature space using a **Gaussian Mixture Model (GMM, K = 5)**.

Rather than directly interpreting GMM clusters as named urban roles, each cluster was mapped using **role-specific scoring rules** based on its feature profile.

#### Role Assignment Logic

- **CBD (Central Business District)**
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

Clusters were mapped to roles by comparing these score profiles.

Station-level role probabilities were then **aggregated from GMM component probabilities**.

Each station was assigned:

- role probabilities
- a final role based on maximum probability

To prevent the largest stations from dominating the interpretation of other roles, the **top 12 stations were treated separately as Mega Hubs**.

#### Role Map

![Role Map](outputs/Role_Map.png)

The spatial pattern is interpretable at the metropolitan scale.

#### Score Map

![Score Map](outputs/Score_Map.png)

The score map suggests that station roles form continuous gradients rather than hard boundaries.

#### Functional Mixing (Entropy)

![Entropy Map](outputs/Entropy_Map.png)

Higher entropy indicates more mixed role characteristics.

---

### 9. Role Distribution

- **Residential:** 279
- **CBD:** 110
- **Transfer Hub:** 62
- **Sub-center:** 23
- **Mega Hub:** 12

---

## Key Insights

- Ridership alone does not fully capture structural importance in urban railway networks.
- Diffused signals reveal hidden structural importance by incorporating neighborhood and network effects.
- Functional roles emerge from a combination of **demand, flow, and structure**, not from scale alone.
- Urban space is better understood as a **continuous functional gradient** than as a fixed set of discrete categories.
- Large hubs shape surrounding stations through network influence.

---

## Contribution

This project contributes:

- a **multi-axis (6D) structural representation** of stations
- a **diffusion-based signal modeling framework**
- a **network-aware interpretation of urban roles**
- an example of combining **spatial data, graph analysis, and unsupervised learning** for urban analytics

---

## Data

- **Ridership data:** 2011–2017
- **Reference year:** 2017
- **Temporal features:** derived from multi-year trends

**Data source:** National Land Numerical Information (MLIT Japan)

- Station data (`N05`)
- Railway sections (`N05`)
- Administrative boundaries (`N03`)
- Ridership (`S12`)
- Population flow (`ju01`)

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

## Limitations

- some feature axes are manually defined
- some correlation remains between axes
- results are sensitive to hyperparameter choices
- classification of smaller stations remains limited

---

## Future Work

- apply the framework to other cities
- improve feature independence
- extend temporal modeling
- explore graph neural network approaches