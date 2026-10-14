"""Train/query separation and grouped threshold semantics guard against leakage."""
import numpy as np
from src.evaluation.ood import DistanceReference,calibration_threshold


def test_query_never_changes_distance_reference():
    train=np.array([[0.,0.],[1.,1.],[2.,3.]])
    ref=DistanceReference().fit(train);before=ref.scaler.mean_.copy()
    score=ref.score(np.array([[.5,.6]]))
    ref.score(np.array([[10000.,-10000.]]))
    np.testing.assert_array_equal(ref.scaler.mean_,before)
    np.testing.assert_array_equal(ref.score(np.array([[.5,.6]])),score)


def test_rotation_pair_is_one_calibration_group():
    # Repeating a rotation must not inflate effective calibration group count.
    scores=np.array([1.,3.,2.,2.]);groups=np.array(['a','a','b','b'])
    value=calibration_threshold(scores,groups,.5)
    duplicated=calibration_threshold(np.repeat(scores,3),np.repeat(groups,3),.5)
    assert value==duplicated==3.
