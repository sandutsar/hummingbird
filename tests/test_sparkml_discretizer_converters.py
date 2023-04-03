"""
Tests Spark-ML discretizer converters: QuantileDiscretizer
"""
import unittest
import warnings

import numpy as np
import torch
from sklearn.datasets import load_iris

from hummingbird.ml._utils import sparkml_installed, pandas_installed
from hummingbird.ml import convert

if sparkml_installed():
    from pyspark.sql import SparkSession, SQLContext
    from pyspark.ml.feature import QuantileDiscretizer

    spark = SparkSession.builder.master("local[*]").config("spark.driver.bindAddress", "127.0.0.1").getOrCreate()
    sql = SQLContext(spark)

if pandas_installed():
    import pandas as pd


class TestSparkMLDiscretizers(unittest.TestCase):
    # Test QuantileDiscretizer
    @unittest.skipIf((not sparkml_installed()) or (not pandas_installed()), reason="Spark-ML test requires pyspark and pandas")
    def test_quantilediscretizer_converter(self):
        iris = load_iris()
        features = ["sepal_length", "sepal_width", "petal_length", "petal_width"]

        pd_df = pd.DataFrame(data=np.c_[iris["data"], iris["target"]], columns=features + ["target"])
        df = sql.createDataFrame(pd_df).select("sepal_length")

        quantile = QuantileDiscretizer(inputCol="sepal_length", outputCol="sepal_length_bucket", numBuckets=2)
        model = quantile.fit(df)

        test_df = df
        torch_model = convert(model, "torch", test_df)
        self.assertTrue(torch_model is not None)

        spark_output = model.transform(test_df).select("sepal_length_bucket").toPandas()
        torch_output_np = torch_model.transform(pd_df[["sepal_length"]])
        np.testing.assert_allclose(spark_output.to_numpy(), torch_output_np, rtol=1e-06, atol=1e-06)


if __name__ == "__main__":
    unittest.main()
