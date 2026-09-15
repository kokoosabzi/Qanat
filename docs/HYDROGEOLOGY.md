# Hydrogeology Stage

This stage provides a provider-neutral inventory for hydrogeology evidence layers:

- geology
- faults/fractures
- wells
- springs
- existing qanats

Inputs are GeoJSON `FeatureCollection` files under `data/raw/hydrogeology/` using the layer filenames above.

The inventory validates GeoJSON structure and records feature counts, geometry types, and optional CRS metadata. It does not infer groundwater occurrence, yield, recharge, or excavation safety.

This foundation is intended for later evidence fusion, ranking, and groundwater-model preparation.
