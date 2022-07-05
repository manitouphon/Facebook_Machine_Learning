import pandas as pd
import apiHandler as ah
import trainerEngine as te
import pandas as pd



class BackEndEngine:
    
    def __init__(self, token):
        self.__token = token
        self.__posts = ah.PostsGrabber(self.__token)
        self.__trainer = te.TrainerEngine()

    def displayTrainData(self, postIter = 3):
        """1 postIter = 25posts. Ex: If postIter = 3, it will try to get at most 75 posts if available"""
        self.__posts.execute(counts= postIter)
        self.__trainer.trainData(dataFrame= self.__posts.getDF())
        self.__trainer.displayDF()
        # self.__trainer.exportCSV()
    def getPageDemographicsData(self):
        return self.__demographics.getDemographics()
    def getTrainedDF(self):
        self.__posts.execute(counts= 0)
        df = self.__posts.getDF()
        if(type(df) is list):
            print("Wrong Token!")
            return df
        self.__trainer.trainData(dataFrame= df )
        return self.__trainer.getDF()
    def getTestTrainedDF(self):
        self.__trainer.trainData()
        return self.__trainer.getDF()



### BELOW CODES ARE USE FOR DEBUG PURPOSE ONLY!:
##### SHOULD NOT EXIST WHEN PRODUCTION!


# token = "INSERT_REAL_ACCESS_OR_LONG_LIVED_TOKEN_HERE"


# eng = BackEndEngine(token= token)


# eng.displayTrainData()






