# -*- coding: utf-8 -*-
"""Graduation ProjectMain.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17cLohP7HkXexz0rrWmBDvjh5GpOZXxAX

# Read the data
"""

import pandas as pd

from google.colab import drive
drive.mount('/content/drive')

housing = pd.read_csv("/content/drive/MyDrive/Graduation Project/Data/housing.csv")

housing

"""# Step 1: Initial Data Exploration"""

housing.info()

housing.shape

housing.columns

housing["ocean_proximity"].value_counts()

housing.describe()

housing.describe(include="O") #include="O" specifies only object columns

import matplotlib.pyplot as plt
housing.hist(bins=50, figsize=(20,15));

"""#Step 2: Split the Data

###**2.1Train And Test sets**###
"""

from sklearn.model_selection import train_test_split

train_set, test_set = train_test_split(housing, test_size=0.2, random_state=42)

train_set, val_set = train_test_split(train_set, test_size=0.25, random_state=42)  # 0.25 of 0.8 = 20%

print("Train Set Shape:", train_set.shape)
print("Validation Set Shape:", val_set.shape)
print("Test Set Shape:", test_set.shape)

train_set_eda = train_set.copy()

"""# Step 3: Discover and Visualize the Data to Gain Insights

###**3.1 Visualizing Geographical Data**
"""

import seaborn as sns
import matplotlib.pyplot as plt
train_set_eda.plot(kind="scatter", x="longitude", y="latitude");

train_set_eda.plot(kind="scatter", x="longitude", y="latitude", alpha=0.1);

train_set_eda.plot(kind="scatter", x="longitude", y="latitude", alpha=0.4,
             s=train_set_eda["population"]/100, label="population", figsize=(10,7),
             c="median_house_value", cmap=plt.get_cmap("jet"), colorbar=True,
             sharex=False);

"""###**3.2 Looking for Correlations**"""

numeric_columns = train_set_eda.select_dtypes(include=['float64', 'int64'])
correlation_matrix = numeric_columns.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
plt.title("Correlation Heatmap of Numeric Features")
plt.show()

correlation_matrix["median_house_value"].sort_values(ascending=False)

attributes = ["median_house_value", "median_income", "total_rooms", "housing_median_age"]

import seaborn as sns
sns.pairplot(train_set_eda[attributes]);

train_set_eda.plot(kind="scatter", x="median_income", y="median_house_value", alpha=0.1);

print(train_set_eda.columns)
train_set_eda.head(1)

"""###**3.3 Experimenting with Attribute Combinations**"""

train_set_eda['rooms_per_household'] = train_set_eda['total_rooms'] / train_set_eda['households']
train_set_eda['bedrooms_per_room'] = train_set_eda['total_bedrooms'] / train_set_eda['total_rooms']
train_set_eda['population_per_household'] = train_set_eda['population'] / train_set_eda['households']

correlation_matrix = train_set_eda.select_dtypes(include=['float64', 'int64']).corr()
correlation_matrix["median_house_value"].sort_values(ascending=False)

"""#Step 4: Prepare the Data for Machine Learning Algorithms

###**4.1 Data Cleaning**###
"""

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class TotalBedroomsMedianFiller(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.median_ = None

    def fit(self, X, y=None):
        # Calculate the median of the 'total_bedrooms' column
        self.median_ = X["total_bedrooms"].median()
        return self

    def transform(self, X):
        # Fill missing values in the 'total_bedrooms' column with the calculated median
        X_copy = X.copy()
        X_copy["total_bedrooms"] = X_copy["total_bedrooms"].fillna(self.median_)
        return X_copy

"""### **4.2 One-Hot Encoding**###"""

from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd

class OceanProximityOneHotEncoder(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.encoded_columns = None

    def fit(self, X, y=None):
        # Get the one-hot encoded column names
        self.encoded_columns = pd.get_dummies(X["ocean_proximity"], drop_first=True).columns.tolist()
        return self

    def transform(self, X):
        # Perform one-hot encoding and drop the original column
        X_copy = X.copy()
        one_hot_encoded = pd.get_dummies(X_copy["ocean_proximity"], drop_first=True)
        X_copy = X_copy.drop(columns=["ocean_proximity"])
        X_copy = pd.concat([X_copy, one_hot_encoded], axis=1)
        return X_copy

"""###**4.3Custom Transformers**###"""

from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

rooms_ix, bedrooms_ix, population_ix, households_ix = 3, 4, 5, 6

class CombinedAttributesAdder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Ensure X is a NumPy array
        if isinstance(X, pd.DataFrame):
            X = X.values

        rooms_per_household = X[:, rooms_ix] / X[:, households_ix]
        population_per_household = X[:, population_ix] / X[:, households_ix]
        bedrooms_per_room = X[:, bedrooms_ix] / X[:, rooms_ix]
        return np.c_[X, rooms_per_household, population_per_household, bedrooms_per_room]

"""###**4.4FeatureScaler**###"""

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

class FeatureScaler(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.scaler = StandardScaler()

    def fit(self, X, y=None):
        self.scaler.fit(X)
        return self

    def transform(self, X):
        return self.scaler.transform(X)

"""###**4.5Transformation Pipelines**###"""

# Split X and y
X_train = train_set.drop("median_house_value", axis=1)
y_train = train_set["median_house_value"]

from sklearn.pipeline import Pipeline

full_pipeline = Pipeline([
    ("total_bedrooms_filler", TotalBedroomsMedianFiller()),
    ("ocean_proximity_encoder", OceanProximityOneHotEncoder()),
    ("attribute_adder", CombinedAttributesAdder()),
    ("feature_scaler", FeatureScaler())
])

X_train_prepared = full_pipeline.fit_transform(X_train)

# Split X and y
X_val = val_set.drop("median_house_value", axis=1)
y_val = val_set["median_house_value"]

X_val_prepared = full_pipeline.transform(X_val)

"""#Step 5: Select and Train a Model"""

from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import Ridge

param_distributions = {
    'random_forest': {
        'n_estimators': [50, 100, 200, 300],
        'max_features': ['sqrt', 'log2', None],  # Remove 'auto'
        'max_depth': [None, 10, 20, 30, 40],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    },
    'svr': {
        'C': [0.1, 1, 10, 100],
        'gamma': ['scale', 'auto'],
        'kernel': ['linear', 'rbf', 'poly']
    },
    'ridge': {
        'alpha': [0.1, 1, 10, 100],
        'solver': ['auto', 'svd', 'cholesky', 'lsqr']
    }
}

param_distributions

# Initialize models
models = {
    'random_forest': RandomForestRegressor(random_state=42),
    'svr': SVR(),
    'ridge': Ridge()
}

# Store results
model_results = {}

# Perform Randomized Search for each model
for model_name, model in models.items():
    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_distributions[model_name],
        n_iter=20,  # Number of random parameter combinations to try
        scoring='neg_mean_squared_error',
        cv=3,  # Cross-validation folds
        verbose=1,
        random_state=42,
        n_jobs=-1
    )

    # Fit the search
    search.fit(X_train_prepared, y_train)

    # Save the results for the current model
    model_results[model_name] = {
        'best_estimator': search.best_estimator_,
        'best_params': search.best_params_,
        'best_score': np.sqrt(-search.best_score_),
        'cv_results': search.cv_results_
    }

# Print results for all models
for model_name, results in model_results.items():
    print(f"Model: {model_name}")
    print(f"Best Parameters: {results['best_params']}")
    print(f"Best Validation RMSE: {results['best_score']:.4f}")
    print("\nDetailed CV Results:")
    for i, mean_score in enumerate(results['cv_results']['mean_test_score']):
        print(f"  Combination {i+1}: {results['cv_results']['params'][i]} -> RMSE: {np.sqrt(-mean_score):.4f}")

# Select the best model overall
best_model_name = min(model_results, key=lambda name: model_results[name]['best_score'])
best_model = model_results[best_model_name]['best_estimator']

print(f"\nBest Model: {best_model_name}")
print(f"Best Parameters: {model_results[best_model_name]['best_params']}")
print(f"Best Validation RMSE: {model_results[best_model_name]['best_score']:.4f}")

# Evaluate the best model on the validation set
y_val_predictions = best_model.predict(X_val_prepared)
final_rmse = np.sqrt(mean_squared_error(y_val, y_val_predictions))
print(f"\nFinal RMSE on Validation Set: {final_rmse:.4f}")

"""# Test"""

# Split X and y for the test set
X_test = test_set.drop("median_house_value", axis=1)
y_test = test_set["median_house_value"]

# Prepare the test set
X_test_prepared = full_pipeline.transform(X_test)

# Use the best model to make predictions
test_predictions = best_model.predict(X_test_prepared)

# Add predictions as a new column to the original test data
test_set_with_predictions = test_set.copy()
test_set_with_predictions["predicted_median_house_value"] = test_predictions

test_set_with_predictions

# Save to a CSV file
output_file = "test_set_with_predictions.csv"
test_set_with_predictions.to_csv(output_file, index=False)

print(f"Results saved to {output_file}")
