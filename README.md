# Tokyo Railway Network Analysis

## Overview
This project analyzes the railway network in Tokyo's 23 wards to identify the structural roles of stations beyond simple ridership.

Instead of evaluating stations solely by passenger volume, this study incorporates network structure, spatial context, and diffusion-based signals to uncover hidden functional roles.

---

## Why it Matters

This approach enables:

- Identifying structurally important stations overlooked by ridership
- Understanding urban functional zones beyond administrative boundaries
- Supporting data-driven urban planning and transportation policy

---

## Background

In large metropolitan systems like Tokyo, ridership is often used as the primary indicator of station importance.

However, ridership alone cannot fully capture:
- structural position in the network
- interaction between neighboring stations
- functional differentiation of urban space

This project introduces a structure-aware signal framework to address these limitations.

---

## Key Idea

### Diffused Signal

A signal is constructed by combining:

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

---

### Signal Diffusion

The signal is propagated through the network so that each station reflects not only its own characteristics, but also the influence of nearby stations.

This process is modeled as:

    x(t+1) = α·x₀ + (1−α)·P·x_t

where:
- P is the transition matrix derived from graph connectivity
- α controls how much of the original signal is preserved

This allows the signal to capture both local and global structural effects.

---

## Methodology

### 1. Station Integration
- Station name normalization
- DBSCAN clustering (eps=50m) to merge nearby stations

Final network:
- 486 nodes
- 670 edges

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

---

### 3. Signal Construction

Initially:
- A single signal was used

Limitation:
- Role separation was unclear
- Large hubs dominated surrounding stations (**hub dominance effect**)

Solution:
- Signal decomposed into 7 axes
- Residual excluded → final 6D feature space

---

### 4. Feature Decomposition

Final model uses a 6-dimensional space (excluding residual)

Reason:
- Residual showed high correlation with demand
- Captured scale effects rather than structure
- Introduced redundancy and distortion

---

### 5. Feature Axes

- **Flow**  
  → Local inflow/outflow structure

- **Demand**  
  → Ridership scale and trend

- **Structure**  
  → Network topology and structural importance

- **Transfer**  
  → Interchange functionality

- **Independence**  
  → Relative separation from major hubs

- **Temporal**  
  → Temporal change pattern of station signal

#### Feature Correlation

![Feature Correlation](outputs/Feature_Correlation.png)

The axes are related but not fully redundant.

#### Axis Maps

![Axes Map](outputs/Axes_Map.png)

The maps highlight different spatial dimensions of the Tokyo railway system.

---

### 6. Regression Validation

Regression tests were conducted to compare:

- Ridership
- Diffused signal

Targets:
- betweenness
- closeness
- degree
- k-core
- hub exposure

Results:

| Metric       | Ridership | Signal | Δ |
|-------------|----------|--------|---|
| betweenness | 0.1489   | 0.2422 | +0.0933 |
| closeness   | 0.1148   | 0.1274 | +0.0126 |
| degree      | 0.2245   | 0.2067 | -0.0177 |
| k-core      | 0.0335   | 0.0428 | +0.0093 |
| hub_exp     | 0.1594   | 0.1743 | +0.0149 |

→ Diffused signal generally explains network structure better than ridership

---

### 7. PCA Validation

→ 6D feature space is well preserved (PC1–PC3 explain ~80% of variance)

#### PCA Space

![PCA Space](outputs/PCA_Space.png)

The plot projects the original 6D feature space onto PC1 and PC2.

---

### 8. GMM Clustering and Role Assignment

Stations were first clustered in the 6D feature space using a Gaussian Mixture Model (GMM, K=5).

Rather than directly treating GMM clusters as named urban roles, each cluster was interpreted using **role-specific scoring rules** based on its feature profile.

#### Role Assignment Logic

- **CBD (Central Business District)**
  - high flow, demand, and structure  

- **Transfer Hub**
  - high transfer and connectivity  

- **Sub-center**
  - moderate values with higher independence  

- **Residential**
  - low flow, low structure, higher independence  

Clusters were mapped to roles by comparing these score profiles.

After that, station-level role probabilities were **aggregated from GMM component probabilities**.

Each station was assigned:
- role probabilities
- a final role (maximum probability)

Top 12 stations were separately defined as **Mega Hubs**.

#### Role Map

![Role Map](outputs/Role_Map.png)

The spatial pattern is interpretable at the metropolitan scale.

#### Score Map

![Score Map](outputs/Score_Map.png)

The score map suggests that roles form continuous gradients rather than hard boundaries.

#### Functional Mixing (Entropy)

![Entropy Map](outputs/Entropy_Map.png)

Higher entropy indicates more mixed role characteristics.

---

### 9. Role Distribution

- Residential: 279
- CBD: 110
- Transfer Hub: 62
- Sub-center: 23
- Mega Hub: 12

---

## Key Insights

- Ridership alone fails to capture structural importance in urban networks
- Diffused signals reveal hidden structural importance
- Functional roles emerge from network structure, not just scale
- Urban space is **continuous, not discrete**
- **Large hubs shape surrounding stations through network influence**

---

## Contribution

- Multi-axis (6D) structural representation
- Diffusion-based signal modeling
- Network-aware interpretation of urban roles

---

## Limitations

- Feature axes are manually defined
- Some correlation remains
- Hyperparameter sensitivity
- Small station classification limitations

---

## Data

- Ridership data: 2011–2017
- 2017 used as **reference anchor**
- Temporal features derived from multi-year trends

---

## Future Work

- Apply to other cities
- Improve feature independence
- Extend temporal modeling
- Explore GNN approaches