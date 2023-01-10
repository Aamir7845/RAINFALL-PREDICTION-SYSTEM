# -*- coding: utf-8 -*-
"""my_project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1N_ROHtWv3Tx_FcWJjttk-LIk85RDRcnE
"""

# Commented out IPython magic to ensure Python compatibility.
# essentials
import numpy as np 
import pandas as pd 

# plotting
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
matplotlib.rcParams['figure.dpi'] = 100
sns.set(rc={'figure.figsize':(11.7,8.27)})
sns.set(style="whitegrid")
# %matplotlib inline

# ml
from sklearn.metrics import accuracy_score, recall_score,ConfusionMatrixDisplay, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb
import joblib

def print_col_type(df):
    non_num_df = df.select_dtypes(include=['object'])
    num_df = df.select_dtypes(exclude=['object'])
    '''separates non-numeric and numeric columns'''
    print("Object columns:")
    for col in non_num_df:
        print(f"{col}")
    print("")
    print("Numeric columns:")
    for col in num_df:
        print(f"{col}")

def missing_cols(df):
    '''prints out columns with its amount of missing values with its %'''
    total = 0
    for col in df.columns:
        missing_vals = df[col].isnull().sum()
        pct = df[col].isna().mean() * 100
        total += missing_vals
        if missing_vals != 0:
          print('{} => {} [{}%]'.format(col, df[col].isnull().sum(), round(pct, 2)))
    
    if total == 0:
        print("no missing values")

from google.colab import files
file = files.upload()

train_a = pd.read_csv("/content/region_A_train.csv")
train_b = pd.read_csv("/content/region_B_train.csv")
train_c = pd.read_csv("/content/region_C_train.csv")
train_d = pd.read_csv("/content/region_D_train.csv")
train_e = pd.read_csv("/content/region_E_train.csv")

test_a = pd.read_csv("/content/region_A_test.csv")
test_b = pd.read_csv("/content/region_B_test.csv")
test_c = pd.read_csv("/content/region_C_test.csv")
test_d = pd.read_csv("/content/region_D_test.csv")
test_e = pd.read_csv("/content/region_E_test.csv")

labels_df = pd.read_csv("/content/solution_train.csv")

from google.colab import drive
drive.mount('/content/drive')

train_a.head()

train_a.info()

print_col_type(train_a)

"""##EDA

"""

train_all = pd.concat([train_a ,train_b ,train_c ,train_d ,train_e], keys=["A", "B", "C", "D", "E"])
train_all

train_all_lvls = train_all.reset_index()
train_all_lvls.rename(columns = {"level_0": "region"}, inplace=True)
train_all_lvls.drop(columns=['level_1'], inplace=True)
train_all_lvls.head()

train_all_lvls['region'].nunique()

train_all_lvls.info()

''' train_all_lvls.columns[2:] '''

train_all_lvls.columns[2:]

sns.countplot(x = 'label', data = labels_df, palette="Set1");

fig, axes = plt.subplots(5,2,figsize=(14, 30), dpi=100)

for i, col_name in enumerate(train_all_lvls.columns[2:]):
    if train_all_lvls[col_name].dtype == 'O':
        train_all_lvls.groupby('region')[col_name].hist(ax=axes[i%5][i//5], alpha=0.6);
        axes[i%5][i//5].legend(["A", "B", "C", "D", "E"]);
    else:
        train_all_lvls.groupby('region')[col_name].plot(ax=axes[i%5][i//5], alpha=0.7);
        axes[i%5][i//5].legend();
    axes[i%5][i//5].set_title(f'{col_name}', fontsize=13);
    plt.subplots_adjust(hspace=0.45)

test_all = pd.concat([train_a ,train_b ,train_c ,train_d ,train_e], keys=["A", "B", "C", "D", "E"])
test_all_lvls = test_all.reset_index()
test_all_lvls.rename(columns = {"level_0": "region"}, inplace=True)
test_all_lvls.drop(columns=['level_1'], inplace=True)
test_all_lvls.head()

fig, axes = plt.subplots(5,2,figsize=(14, 30), dpi=100)

for i, col_name in enumerate(test_all_lvls.columns[2:-1]):
    if test_all_lvls[col_name].dtype == 'O':
        test_all_lvls.groupby('region')[col_name].hist(ax=axes[i%5][i//5], alpha=0.4);
        axes[i%5][i//5].legend(["A", "B", "C", "D", "E"]);
    else:
        test_all_lvls.groupby('region')[col_name].plot(ax=axes[i%5][i//5], alpha=0.7);
        axes[i%5][i//5].legend();
    axes[i%5][i//5].set_title(f'{col_name}', fontsize=13);
    plt.subplots_adjust(hspace=0.45)

"""##Missing Values"""

missing_cols(train_all_lvls)

plt.figure(figsize=(10, 6))
sns.heatmap(train_all_lvls.isnull(), yticklabels=False, cmap='viridis', cbar=False);

train_all_lvls['min.atmos.pressure'].hist();

mean_atmos = train_all_lvls['min.atmos.pressure'].mean()
train_all_lvls.fillna(mean_atmos, inplace=True)
missing_cols(train_all_lvls)

missing_cols(test_all_lvls)

test_all_lvls.fillna(mean_atmos, inplace=True)
missing_cols(test_all_lvls)

"""##Feature Engineering"""

train_all_lvls = train_all_lvls.merge(labels_df, on="date")
train_all_lvls.dtypes

le = LabelEncoder()
le.fit(train_all_lvls['label'])
le_name_map = dict(zip(le.classes_, le.transform(le.classes_)))
le_name_map

train_all_lvls.select_dtypes('object').columns

test_all_lvls.select_dtypes('object').columns

BEAUFORT = [
    (0, 0, 0.3),
    (1, 0.3, 1.6),
    (2, 1.6, 3.4),
    (3, 3.4, 5.5),
    (4, 5.5, 8),
    (5, 8, 10.8),
    (6, 10.8, 13.9),
    (7, 13.9, 17.2),
    (8, 17.2, 20.8),
    (9, 20.8, 24.5),
    (10, 24.5, 28.5),
    (11, 28.5, 33),
    (12, 33, 200),
]



def feature_eng(df):
    le = LabelEncoder()
    
    cat_cols = df.select_dtypes("object").columns[2:]

    for col in cat_cols:
        if df[col].dtype == "object":
            df[col] = le.fit_transform(df[col])

    for item in BEAUFORT:
        df.loc[
            (df["avg.wind.speed"] >= item[1]) & (df["avg.wind.speed"] < item[2]),
            "beaufort_scale",
        ] = item[0]

    df['beaufort_scale'] = df['beaufort_scale'].astype(int)

    return df

train = feature_eng(train_all_lvls)
test = feature_eng(test_all_lvls)

"""##Prepare train data"""

train.head()

train.dtypes

train = train.pivot_table(index=["date", "label"], columns="region")
train = pd.DataFrame(train.to_records())
train.head()

def replace_all(text):
    d = { "('": "", "', '": "_", "')" : "",}
    for i, j in d.items():
        text = text.replace(i, j)
    return text

# ('avg.temp', 'A') -> avg.temp_A

test_str = "('avg.temp', 'A')"
replace_all(test_str)

train.columns = list(map(replace_all, train.columns))

train.columns

test = test.pivot_table(index=["date"], columns="region")
test = pd.DataFrame(test.to_records())
test.columns = list(map(replace_all, test.columns))

train

test

"""##Build the LightGBM model





"""

train.dtypes

categoricals = list(train.select_dtypes(include=['int64']).columns)
categoricals.remove("label")
numericals = list(train.select_dtypes(include=['float64']).columns)

feat_cols = categoricals + numericals

X = train[feat_cols]
y = train['label']
 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = 0)

clf = lgb.LGBMClassifier()

clf.fit(X_train, y_train)

"""##Model Prediction"""

y_pred=clf.predict(X_test)

"""##Model performance"""

acc_score = accuracy_score(y_pred, y_test)
recall_score = recall_score(y_pred, y_test, average='macro')
print(f"Accuracy: {acc_score}, recall: {recall_score}")

print(classification_report(y_test, y_pred))

"""##Confusion matrix"""

class_names = le_name_map.keys()

titles_options = [
    ("Confusion matrix, without normalization", None),
    ("Normalized confusion matrix", "true"),
]
for title, normalize in titles_options:
    fig, ax = plt.subplots(figsize=(10, 10))

    disp = ConfusionMatrixDisplay.from_estimator(
        clf,
        X_test,
        y_test,
        display_labels=class_names,
        cmap=plt.cm.Reds,
        normalize=normalize,
        ax = ax
    )
    disp.ax_.set_title(title)
    disp.ax_.grid(False)

    print(title)
    print(disp.confusion_matrix)

"""##Check for overfitting"""

print('Training set score: {:.4f}'.format(clf.score(X_train, y_train)))
print('Test set score: {:.4f}'.format(clf.score(X_test, y_test)))

"""##Feature importance"""

feature_imp = pd.DataFrame(sorted(zip(clf.feature_importances_,X.columns)), columns=['Value','Feature'])

plt.figure(figsize=(20, 10))
sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value", ascending=False))
plt.title('LightGBM Features')
plt.tight_layout()
# plt.savefig('lightgbm_fimp.png')

"""##Save the model"""

joblib.dump(clf, 'lgb1.pkl')

"""##Predict on test data"""

X = test[feat_cols]

test_preds = clf.predict(X)
submission_df = pd.concat([test['date'], pd.DataFrame(test_preds, columns=['label'])], axis=1)
submission_df.head()

le_name_map

inv_map = {v: k for k, v in le_name_map.items()}
inv_map

submission_df['label'] = submission_df['label'].map(inv_map)  
submission_df.head()

"""## Solution file"""

submission_df.to_csv('solution.csv', index=False)