import * as introduction from './introduction.js';
import * as eda from './eda.js';
import * as clustering from './clustering.js';
import * as pca from './pca.js';
import * as placeholder from './placeholder.js';

// Every chapter supplies render(data) and init(data). init may return a cleanup function.
export const chapters = [
  {title:'Introduction', heading:'Introduction: Making Sense of the Flux', slug:'introduction', ...introduction},
  {title:'Data Prep + EDA', heading:'Data Preparation and Exploration: Surface-level Insights', slug:'data-prep-eda', ...eda},
  {title:'Clustering', heading:'Clustering: Discovering County Profiles', slug:'clustering', ...clustering},
  {title:'PCA', heading:'Principal Component Analysis: Reducing Features into Key Dimensions', slug:'pca', ...pca},
  {title:'NaiveBayes', heading:'NaiveBayes', slug:'naivebayes', ...placeholder},
  {title:'DecTrees', heading:'DecTrees', slug:'dectrees', ...placeholder},
  {title:'Regression', heading:'Regression', slug:'regression', ...placeholder},
  {title:'AdaBoost', heading:'AdaBoost', slug:'adaboost', ...placeholder},
  {title:'GradientBoosting', heading:'GradientBoosting', slug:'gradientboosting', ...placeholder},
  {title:'XGBoost', heading:'XGBoost', slug:'xgboost', ...placeholder},
  {title:'Conclusion', heading:'Conclusion', slug:'conclusion', ...placeholder},
];
