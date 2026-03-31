# Tokyo Railway Network Analysis

## Overview
This project analyzes the railway network in Tokyo's 23 wards to identify the structural roles of stations beyond simple ridership.

Instead of evaluating stations solely by passenger volume, this study incorporates network structure, spatial context, and diffusion-based signals to uncover hidden functional roles.



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
- ridership
- urban flow characteristics
- network structure

This signal is then diffused over the network to incorporate neighborhood effects.

---

## Methodology

### 1. Station Integration
- Station name normalization
- DBSCAN clustering (eps=50m) to merge nearby stations

Final network:
- 486 nodes
- 670 edges

---

### 2. Signal Decomposition

Initially:
- A single signal was used

Limitation:
- Role separation was unclear

Solution:
- Signal decomposed into 7 axes
- Residual excluded → final 6D feature space

---

### 3. Feature Space Design

Final model uses a 6-dimensional space (excluding residual)

Reason:
- Residual showed high correlation with demand
- Captured scale effects rather than structure
- Introduced redundancy and distortion

Example:
- Large stations (e.g., Shinjuku) contain extreme demand not explained by network structure
- This effect appears in both demand and residual → duplication

---

### 4. Feature Axes

- Flow  
  → Spatial inflow/outflow structure

- Demand  
  → Absolute passenger volume

- Structure  
  → Network centrality, connectivity, and hub exposure

- Transfer  
  → Interchange functionality

- Independence  
  → Isolation from major hubs

- Temporal  
  → Signal change pattern (growth, slope, stability)

---

### 5. Clustering

- Gaussian Mixture Model (K=5)
- Probabilistic clustering

Cluster → Role mapping:

- CBD
- Transfer Hub
- Sub-center
- Residential

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

### 7. Role Distribution

Final classification:

- Residential: 279
- CBD: 110
- Transfer Hub: 62
- Sub-center: 23
- Mega Hub: 12

---

### 8. PCA Validation

- PC1: 0.4595
- PC2: 0.2091
- PC3: 0.1372  
- Total (PC1~3): 0.8058

→ 6D structure is well preserved in low-dimensional space

---

## Visualization

### 1. Axis Interpretation

![Axes Map](outputs/Axes_Map.png)
![Feature Correlation](outputs/Feature_Correlation.png)

---

### 2. Role Classification

![Role Map](outputs/Role_Map.png)
![Score Map](outputs/Score_Map.png)
![Entropy Map](outputs/Entropy_Map.png)

---

### 3. Validation

![PCA Space](outputs/PCA_Space.png)

---

## Key Insights

- Ridership alone fails to capture structural importance in urban networks
- Diffused signals reveal stations that are critical for network connectivity despite lower demand
- Functional roles of stations emerge from network structure rather than absolute scale
- Urban space can be interpreted as a combination of interacting roles, not discrete categories

---

## Limitations

- Feature axes are manually defined → not fully independent
- Some correlation remains between axes
- Results depend on hyperparameters (DBSCAN, diffusion, GMM)
- Trade-off between interpretability and statistical optimality
- The role classification of some smaller stations is insufficient

---

## Files

- `tokyo-railway-network-analysis`: main analysis pipeline
- `outputs/`: visualization results

---

## Data

National Land Numerical Information (MLIT Japan)

- Station data (N05)
- Railway sections (N05)
- Administrative boundaries (N03)
- Ridership (S12)
- Population flow (ju01)

Download:
http://nlftp.mlit.go.jp/ksj/

---

## Future Work

- Apply to other cities
- Improve feature independence
- Incorporate temporal dynamics more explicitly
- Explore GNN-based extensions