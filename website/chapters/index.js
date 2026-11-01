import * as introduction from './introduction.js';
import * as findings from './findings.js';
import * as eda from './eda.js';
import * as clustering from './clustering.js';
import * as pca from './pca.js';
import * as naiveBayes from './naive-bayes.js';
import * as decisionTrees from './decision-trees.js';
import * as placeholder from './placeholder.js';

// Dependencies are loaded on chapter entry. init may return a cleanup function.
export const chapters = [
  {title:'Overview', heading:'County Characteristics and Migration Flows', slug:'introduction', group:'Overview', status:'complete', datasets:['intro','findings','population','geo','states'], ...introduction},
  {title:'Findings and limitations', heading:'What the Evidence Shows', slug:'conclusion', group:'Findings', status:'complete', datasets:['intro','findings'], ...findings},
  {title:'Clustering', heading:'Clustering: Discovering County Profiles', slug:'clustering', group:'Analyses', status:'complete', datasets:['clusteringResults','geo','states'], ...clustering},
  {title:'PCA', heading:'Principal Component Analysis: Dimensions of County Characteristics', slug:'pca', group:'Analyses', status:'complete', datasets:['pcaResults'], ...pca},
  {title:'Naive Bayes', heading:'Naive Bayes: Classifying Inflow Intensity', slug:'naivebayes', group:'Analyses', status:'complete', datasets:['naiveBayesResults'], ...naiveBayes},
  {title:'Decision Trees', heading:'Decision Trees: Classifying Outflow and Net Direction', slug:'dectrees', group:'Analyses', status:'complete', datasets:['decisionTreeResults'], ...decisionTrees},
  {title:'Exploration and data', heading:'Migration Patterns and Their Data Foundations', slug:'data-prep-eda', group:'Data & Methods', status:'complete', datasets:['analysis','cleaningEvidence','geo','states'], ...eda},
  ...[['Regression','regression'],['AdaBoost','adaboost'],['Gradient boosting','gradientboosting'],['XGBoost','xgboost']].map(([title,slug])=>({title,heading:title,slug,group:'Future work',status:'planned',datasets:[],render:()=>placeholder.render(title),init:placeholder.init})),
];

export const datasets = {
  intro:'introduction.json', findings:'findings.json', population:'population.json', geo:'county.geojson', states:'state.geojson',
  analysis:'exploration/analysis.json', cleaningEvidence:'cleaning/cleaning-evidence.json',
  clusteringResults:'clustering/clustering.json', pcaResults:'pca/pca.json',
  naiveBayesResults:'classification/naive-bayes.json', decisionTreeResults:'classification/decision-trees.json',
};
