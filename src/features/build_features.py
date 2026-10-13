"""Geometry-only descriptors. Never read temperature/flux/label to build ML inputs."""
import numpy as np
from scipy.ndimage import distance_transform_edt,label

FEATURES_NO1=['porosity','interface_density','mean_pore_diameter_px','anisotropy',
              'solid_span_fraction','pore_largest_fraction','bottleneck','section_cv','straight_solid_fraction']

def spanning_fraction(mask):
    components,n=label(mask)
    ids=np.intersect1d(np.unique(components[:,0]),np.unique(components[:,-1]))
    ids=ids[ids>0]
    return float(np.isin(components,ids).sum()/max(mask.sum(),1))

def descriptors(solid):
    s=np.asarray(solid,dtype=bool);p=~s
    ix=float((s[:,1:]!=s[:,:-1]).mean());iy=float((s[1:,:]!=s[:-1,:]).mean())
    # Pad with solid to define a reproducible image-boundary convention for pore radii.
    dist=distance_transform_edt(np.pad(p,1,constant_values=False))[1:-1,1:-1]
    labs,n=label(p);sizes=np.bincount(labs.ravel())[1:]
    sec=s.mean(axis=0);mean=sec.mean()
    return dict(porosity=float(p.mean()),interface_density=(ix+iy)/2,
                mean_pore_diameter_px=float(2*dist[p].mean()) if p.any() else 0.,
                anisotropy=(iy-ix)/max(iy+ix,1e-15),
                solid_span_fraction=spanning_fraction(s),
                pore_largest_fraction=float(sizes.max()/p.sum()) if len(sizes) else 0.,
                bottleneck=float(sec.min()/max(mean,1e-15)),
                section_cv=float(sec.std()/max(mean,1e-15)),
                straight_solid_fraction=float(s.all(axis=1).mean()))
