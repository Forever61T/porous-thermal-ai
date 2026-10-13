"""Simple fixed CPU estimators; scaler is fitted on training rows inside Pipeline."""
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor

def estimator(kind,cfg,seed):
    if kind=='Ridge':return make_pipeline(StandardScaler(),Ridge(alpha=cfg['ridge_alpha']))
    if kind=='RF':return RandomForestRegressor(n_estimators=cfg['rf_trees'],min_samples_leaf=cfg['rf_min_leaf'],
                                                random_state=seed,n_jobs=cfg['rf_jobs'])
    raise ValueError(kind)
