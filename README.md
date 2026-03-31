# Tokyo Railway Network Analysis

## Overview
This project analyzes the railway network in Tokyo's 23 wards to identify the structural roles of stations beyond simple ridership.

Instead of evaluating stations solely by passenger volume, this study incorporates network structure, spatial context, and flow dynamics to uncover hidden functional roles.

---

## Background

In large metropolitan systems like Tokyo, ridership is often used as the primary indicator of station importance.

However, ridership alone cannot fully capture:
- structural position in the network
- flow dynamics between regions
- functional differences between stations

This project aims to overcome these limitations by introducing a **structure-aware signal framework**.

---

## Key Idea

### 1. Diffused Signal (Structure-aware signal)

A signal is constructed by combining ridership with:
- urban flow characteristics
- network topology
- spatial structure

Then, diffusion is applied over the network to incorporate neighborhood effects.

---

### 2. Validation (Regression Test)

To validate the usefulness of the signal:

- Regression analysis was conducted between:
  - **ridership**
  - **diffused signal**

Result:
- Diffused signal explains network structure **better than raw ridership**
- Demonstrates that structural information is successfully embedded

---

## Methodology

### 1. Station Integration
- Station name normalization
- DBSCAN clustering to merge nearby stations

---

### 2. Signal Decomposition

Initially:
- A single composite signal was used

Problem:
- Different roles were not clearly separable

Solution:
- Signal was decomposed into **7 axes**
- Reconstructed into a **multi-dimensional feature space**

---

### 3. Feature Space Design

The initial signal was decomposed into 7 axes.
However, the final model uses a **6-dimensional feature space**, excluding the residual axis.

Reason:
- The residual component showed high correlation with demand
- It captured scale-driven effects rather than structural characteristics
- Including it introduced redundancy and distorted the structural interpretation

For example, large stations (e.g., Shinjuku) exhibit extreme demand levels that cannot be explained purely by network structure.
These scale effects were reflected in both demand and residual, leading to duplication.

Therefore, removing the residual axis improved the clarity and interpretability of the feature space.

---

### 4. Feature Axes (Core Concepts)

- **Flow**  
  → Relative inflow/outflow structure in the urban-network context

- **Demand**  
  → Absolute passenger volume

- **Structure**  
  → Network position such as centrality and connectivity

- **Transfer**  
  → Degree of interchange functionality

- **Independence**  
  → Relative isolation from dominant hubs

- **Temporal**  
  → Temporal variation pattern derived from signal growth, slope, and stability

- **Residual (excluded)**  
  → Non-structural demand component, excluded due to overlap with demand

---

### 5. Clustering (GMM)

- Gaussian Mixture Model applied
- Each station assigned **probabilistic cluster membership**

---

### 6. Role Assignment

Clusters are interpreted as functional roles:

- Mega Hub
- Business Core
- Subcenter
- Residential Area
- Transfer Hub

Each station receives:
- role probabilities
- role-based scores

---

### 7. Entropy (Role Mixing)

Entropy is calculated from cluster probabilities:

- High entropy → mixed role
- Low entropy → clear role

---

### 8. Validation (PCA Projection)

- 6D feature space projected into 2D using PCA
- Used only for **validation and visualization**

Important:
- PCA is NOT used for modeling
- Maintains interpretability of manually defined axes

---

## Results

- Stations can be classified into distinct functional roles
- Structural importance differs from ridership ranking
- Some low-demand stations have high structural significance
- High-demand stations may contain non-structural scale effects

---

## Visualization

![Network Map](outputs/network_map.png)
![Role Classification](outputs/role_classification.png)

---

## Key Insights

- Ridership alone is insufficient to explain station roles
- Network diffusion captures hidden structural importance
- Multi-dimensional decomposition is necessary for role separation
- Probabilistic clustering enables flexible role interpretation

---

## Limitations

- Feature axes are manually defined → not fully independent
- PCA improves accuracy but reduces interpretability
- Trade-off between:
  - explainability
  - statistical optimality

---

## Files

- `tokyo-railway-network-analysis.py`: main analysis pipeline
- `outputs/`: visualization results

---

## Data

This project uses National Land Numerical Information (MLIT Japan).

Data source:
http://nlftp.mlit.go.jp/ksj/

Raw data is not included in this repository.

---

## Future Work

- Apply to other metropolitan areas
- Integrate temporal dynamics
- Improve feature independence
- Explore graph-based deep learning models (GNN)
