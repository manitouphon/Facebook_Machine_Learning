# Import pandas library
import os.path  #for checking files' and paths
import pandas as pd #pandas for dealing with CSV
import numpy as np  #Numpy for dealing with np array
import pickle as pk #Dumping Learning model as binary 
from tabulate import tabulate

import texthero as hero #text cleaning
from sklearn.feature_extraction.text import CountVectorizer #Bags of word vectorizer
from sklearn.utils import shuffle #shuffle dataset
from sklearn.naive_bayes import MultinomialNB 


from sklearn.model_selection import train_test_split
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation

from sklearn.feature_extraction.text import TfidfVectorizer

from imblearn.over_sampling import SMOTE 

# Class

class TrainerEngine:
    def trainData(self, dataFrame = None):
        df = pd.read_csv(
            'https://raw.githubusercontent.com/manitouphon/huff-post-csv-news-category-dataset/main/simplified_data.csv',
            sep=',',
            usecols=["category", "headline"],
            )
        if (dataFrame is not None):
            target_df = dataFrame
            target_df["TITLE"] = target_df["message"]
            target_df.pop("message")
            print("DF = 1")
        else:
            print("DF = 0")
        ## Testing Data
            target_df = pd.read_csv(
                'https://raw.githubusercontent.com/manitouphon/FaceMine-backend/main/PPPostFBScrape.csv',
                sep=',',
                usecols=["TITLE"],
                )
            
            target_df.drop_duplicates(subset="TITLE", keep=False)
            
        
        
        df["headline"] = hero.clean(df["headline"])
        headlineArr = df["headline"].array
        df = shuffle(df)

        x = np.array(df["headline"])
        y = np.array(df["category"])

       

        vectorizer = CountVectorizer()
        # x = count_vec.transform(x)
        # vectorizer=TfidfVectorizer(stop_words='english') 
        x = vectorizer.fit_transform(x)


        # # Resample data
        # sm = SMOTE()
        # x, y = sm.fit_resample(x, y)
        # unique, counts = np.unique(y, return_counts=True)
        # print(unique, counts)

        

        model_filename = r"nb_model.sav"
        if(os.path.isfile(model_filename)): #check if file exists
            with open(model_filename, "rb") as model:
                loaded_model = pk.load(model)  #load
            print("load model successfully! ")
        else:
            print("No model found ... Making a new One ....")
            
            #   Train with test then show the acc and metrics 
            nb_model = MultinomialNB()
            x_train, x_test, y_train, y_test = train_test_split(x,y, test_size=0.3 , random_state=10)
            nb_model.fit(x_train,y_train)
            y_predict = nb_model.predict(x_test)
            acc = metrics.accuracy_score(y_test, y_predict)
            metric = metrics.confusion_matrix(y_test, y_predict )
            f1 = metrics.f1_score(y_test, y_predict, average=None)
            # f1_avg = metrics.f1_score(y_test, y_predict)
            print("Total Numbers of Categories: ", df["category"].nunique(),"\n", df["category"].value_counts())
            print("F1 Score:", f1  ,"Acc",acc, "\n",metric)

            nb_model.fit(x_train,y_train)
            
            loaded_model = nb_model
            # Dump Model to a file after training 
            # pk.dump(nb_model, open(r"nb_model.sav", "wb"))  
            
        target_df["CLEANED"] = hero.clean( target_df["TITLE"])  #init CLEAN column
        title = target_df["CLEANED"].tolist()
        cat = [None] * len(title)  #init list with size = len(df[title])



        trained = pd.DataFrame(columns=["title","category"])
        for x in range ( len(title) ):
            if (title[x].lower() == "none"):
                cat[x] = "NONE"
                continue
            data = vectorizer.transform([title[x]]).toarray()
            cat[x] = loaded_model.predict(data)[0]
        target_df["CATEGORY"] = cat
        target_df.pop("CLEANED")
        target_df.insert(0,"Category",target_df.pop("CATEGORY") )
        target_df.insert(0,"Caption",target_df.pop("TITLE") )
        
        self.__trainedDF = target_df
        print("Training Finished")
        

    def getDF(self):
        return self.__trainedDF
    def displayDF(self):
        print(tabulate(self.__trainedDF, headers = 'keys', tablefmt = 'psql'))
    def exportCSV(self):
        self.__trainedDF.to_csv('trained.csv', index=False)