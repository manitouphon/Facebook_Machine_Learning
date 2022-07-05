import json
from time import time
import requests 
import pandas as pd
from tqdm import tqdm as progressRep
from tabulate import tabulate
from furl import furl 
from datetime import datetime
import re


TARGET_TIME = time()
    

class PostsGrabber:
    """
        How to use:
            -initiate an object and pass token as a string in the parameter
            -call the execute(x) to init data grabbing ( 1 * x = 25 posts. Ex: if x = 3 ==> it will try to get 75 posts if available)
            -after calling the execute(), you could use getDF to get DataFramee object
    """

    __baseURL="https://graph.facebook.com/v13.0/"
    __ALLOW = False
    __df = pd.DataFrame()
    __messages = []
    __id = []
    __score = []
    __reactions = []
    __comments = []
    __shares = []


    __path="posts?fields=message,insights.metric(post_impressions, post_clicks, post_negative_feedback),shares,reactions.summary(true),comments.summary(true)"


    #DEBUG
    def displayDataFrame(self):
        print(tabulate(self.__df, headers = 'keys', tablefmt = 'psql'))

    def exportCSV(self):
        self.__df.to_csv("Posts.csv", sep='\t')

    #END of DEBUG

    def __init__(self, token):
        self.__id = "me"
        self.__token = token
    def __checkReturnAllowance(self,item):
        if(self.__ALLOW):
            return item
        else:
            print("Error@Class \"apiHandler.PostsGrabber\"\n\n", "Reason: Please call the execute() function first")
            return "Error"

    def __getNext(self, url = None ):
        if( url is None):
            # Craft the target request URL
            requestURL=self.__baseURL + self.__id + "/" + self.__path + "&access_token=" + self.__token      
        else:
            requestURL = url
        htmlRespond = requests.get(requestURL)
        if 200 <= htmlRespond.status_code <= 299:
            data = htmlRespond.text
            parsed = json.loads(data)
            return parsed
        else:
            return {"data" : "failed", "respond": htmlRespond.text}


    # def __exportJSON(self):
    #     export = {"messages":self.__messages, "insights": self.__insights}

    #     with open('post_export.json', 'w') as file:
    #         json.dump(export, file, indent=4)
        



    def __loadMessage(self):
        parsed = self.__data
        data = {"data":parsed}
        list = [None] * len(data["data"])
        id = [None] * len(data["data"])
        for x in progressRep(range (len(data["data"])), desc="Load Messages"):
            id[x] = "https://Facebook.com/" + data["data"][x]["id"]
            if("message" in data["data"][x]):
                list[x] = data["data"][x]["message"]
            else:
                list[x] = "None"
        self.__messages = list 
        self.__id =  id
        # print("DEBUG Message:",self.__message)

    


    # insights format [impressions,engaged_users, negative_feedback]
    def __loadInsights(self):
        parsed = self.__data  
        data = {"data": parsed}
        result = []
        tmp = []
        views = []
        clicks = []
        negative_feedback = []
        print("DEBUG:", json.dumps(data, indent=4))
        for x in progressRep(range (len(data["data"])), desc="Load Insights",):
            tmp=[]
            data2 = {"data" : data["data"][x]}
            data2 = {"insights": data2["data"]["insights"]}
            data2 = {"data": data2["insights"]["data"]}
            for y in range (len( data2["data"] )):
                tmp.append(data2["data"][y]["values"][0]["value"])
            result.append(tmp)

        for x in range(len(result)):
            views.append( result[x][0] )
            clicks.append( result[x][1] )
            negative_feedback.append( result[x][2] )

        # print(json.dumps(result))
        self.__views = views
        self.__clicks = clicks
        self.__negative_feedback = negative_feedback


    def __loadScore(self):
        data = {"data": self.__data}
        reactions = [None] * len(data["data"])
        comments = [None] * len(data["data"])
        shares = [None] * len(data["data"])

        score = [None] * len(data["data"])

        for x in progressRep(range(len(data["data"])),desc="Load Score", ):
            reactions[x] = data["data"][x]["reactions"]["summary"]["total_count"]
            comments[x] = data["data"][x]["comments"]["summary"]["total_count"]
            if( "shares" in data["data"][x]):
                shares[x] = data["data"][x]["shares"]["count"]
            else:
                shares[x] = 0
            #initiate scoring 
            score[x] = (reactions[x] * 1.1) + (comments[x] * 1.4) + (shares[x] * 1.2) + self.__clicks[x]

            
        self.__score = score
        # print("DEBUGGING 1:",reactions,comments,shares,score)

            

    def __finalizedData(self):
        self.__loadMessage()
        self.__loadInsights()
        self.__loadScore()
        # print(self.__insights, type(self.__insights))
        self.__df["message"] = self.__messages
        self.__df["Engagement score"] = self.__score
        self.__df["Views"] = self.__views
        self.__df["Clicks"] = self.__clicks
        self.__df["negative feedback"] = self.__negative_feedback
        self.__df["post link"] =  self.__id

        self.__df =  self.__df.sort_values(by ="Engagement score",ascending=False)
        
        # self.displayDataFrame()
    
        
    
    #public Def
    def getCaptions(self):
        return self.__checkReturnAllowance(self.__messages)
    def getDF(self):
        print(type(self.__df))
        return self.__checkReturnAllowance(self.__df)


    # Since counts = 1 has 25 posts 
    def execute(self, counts = 3):
        if counts == 0:
            counts = 1000
        parsed = self.__getNext()
        if(parsed["data"] == 'failed'):
            print("FAILED.", "Respond Message: \n\n", parsed["respond"])
            self.__ALLOW = True
            self.__df = [parsed, False]
            return [parsed, False]
        data = parsed["data"]
    

      
        for x in progressRep(range(counts), desc="Getting Posts ...", unit="25posts"):
            if( "next" in parsed["paging"]):
                nextParsed = self.__getNext(parsed["paging"]["next"])
                data = ( data + nextParsed["data"])
                parsed = nextParsed
            else:
                break
                
          
        
        self.__data = data
        self.__finalizedData()
        self.__ALLOW = True
        return data

    


































class PageDemographic:
    __baseURL="https://graph.facebook.com/v13.0/"
    __df = pd.DataFrame()


    def __init__(self, token):
        self.__id = "me"
        self.__token = token
        self.__ALLOW = (self.__getTotalFan() >= 100)
        if(self.__ALLOW is False):
            print("Warning! Your page has less than 100 total likes, which Facebook will forbids you from accessing demographics data")

    
   

    def __getParsedData(self, path = "", url = None):
        if( url is None):
            # Craft the target request URL
            requestURL=self.__baseURL + self.__id + "/" + path + "&access_token=" + self.__token      
        else:
            requestURL = url
        htmlRespond = requests.get(requestURL)
        if 200 <= htmlRespond.status_code <= 299:
            data = htmlRespond.text
            parsed = json.loads(data)
            return parsed
        else:
            return {"data" : "failed", "respond": htmlRespond.text}
    def __lastNextPagging(self, parsed):
        # Keep navigating pagging->next until hit the last one
        countsLimiter = 0
        while(True):
            if( "next" in parsed["paging"]):
                nextParsed = self.__getParsedData(url = parsed["paging"]["next"])
                if (len(nextParsed["data"]) == 0):
                    print("Breaking")
                    break
                url = parsed["paging"]["next"]
                parsed = nextParsed
            else:
                break
            countsLimiter = countsLimiter + 1
        return [parsed, url]

       
       
    # Get Total Fans:
    def __getTotalFan(self):
        path = "insights?metric=page_fans"
        parsed = self.__getParsedData(path = path)      
        if(parsed["data"] == 'failed'):
            print("FAILED.", "Respond Message: \n\n", parsed["respond"])
            return ""

        url = parsed["paging"]["next"]
        f = furl(url)
        del f.args["until"]
        f.args["since"] = TARGET_TIME
        
        value = parsed["data"][0]["values"][0]["value"]
        return value

     



    # Fan's City 
    def __getCity(self):
        path = "insights?metric=page_fans_city"
        
        parsed = self.__getParsedData(path = path)

        lastPagging = self.__lastNextPagging(parsed= parsed)
        url = lastPagging[1]
        parsed = lastPagging[0]
        
        f = furl(url)
        del f.args["until"]

        parsed = self.__getParsedData(url = f.url)
        total_fans = self.__getTotalFan()    

  

        data = parsed["data"]
        items = data[0]["values"][0]["value"]

        keys = list(items.keys()) 
        values = list(items.values())
        percentage = [None] * len(values)

        for x in (range(len(values))):
            if ("," in keys[x] )is False:
                keys[x] = keys[x] + ", Cambodia"
            if ("-" in keys[x] ):
                keys[x] = keys[x].replace("-", " ")
            percentage[x] = "{:.2f}".format(values[x] / total_fans * 100.0)
            

        
        
        self.__city = [keys,values,percentage]
        #DEBUG:
        # print(self.__city)

        
        # Testing Geocoding
        # NEED ASYNCIO or Multi-Threading AS SOON AS POSSIBLE!
        print("coor = [")
        lat_ = [None] * len(keys)
        long_ = [None] * len(keys)

        for x in range(len(keys)):
            parameters = {
                "key": "19407rdTEtTVYwQEUlIy1gTzhT8AIi3R",
                "location": keys[x]
            }
            response = requests.get("http://www.mapquestapi.com/geocoding/v1/address", params=parameters)
            data = response.text
            dataJ = json.loads(data)['results']
            lat = (dataJ[0]['locations'][0]['latLng']['lat'])
            lng = (dataJ[0]['locations'][0]['latLng']['lng'])
            print("[\"",keys[x], "\",",lat, ",",lng,"],")
            lat_[x] = lat
            long_[x] = lng
            
        self.__lat = lat_
        self.__long = long_
        print("]\n\n values = [")


        for x in range(len(values)):
            print("[",values[x], ",",percentage[x],"],")
        print("]")


 
    
    # New likes and dislikes 
    def __getFansAddnRemove(self):
        path = "insights?metric=page_fan_adds,page_fan_removes&period=day"
        add = [None] * 30
        remove = [None] * 30
        add_timestamp = [None] * 30
        remove_timestamp = [None] * 30

        parsed = self.__getParsedData(path = path)
        # Traverse to the last next url in pagging. Will return [parsed, url]
        lastPagging = self.__lastNextPagging(parsed)
        url = lastPagging[1]
        parsed = lastPagging[0]
    
        #manipulate URL param (Revert param[since] back 30 days)
        f = furl(url)
        f.args["since"] = int(f.args["since"]) - (86400*30)

        # getParsedData for the new url with modified "since" parameter
        parsed = self.__getParsedData(url = f)
        # Assign to list
        for x in progressRep(range(0,30), desc="New Likes and Removed Likes"):
            add[x] = parsed["data"][0]["values"][x]["value"]
            remove[x] = parsed["data"][1]["values"][x]["value"]
            #convert timestamps for display
            time = parsed["data"][0]["values"][x]["end_time"]
            time = time[0:10]
            date = datetime.strptime(time,'%Y-%m-%d')
            date = date.strftime("%b-%d")
            add_timestamp[x] = date

            time = parsed["data"][1]["values"][x]["end_time"]
            time = time[0:10]
            date = datetime.strptime(time,'%Y-%m-%d')
            date = date.strftime("%b-%d")
            remove_timestamp[x] = date

    

        self.__newLikes = [add_timestamp,add] 
        self.__newRemovedLikes =[remove_timestamp, remove]
        # DEBUG:
        # print(self.__newLikes, self.__newRemovedLikes)




    # Fan's Gender Demographics
    def __getPageFansGender(self):
        path = "insights?metric=page_fans_gender_age"
        
        parsed = self.__getParsedData(path = path)
        if(parsed["data"] == 'failed'):
            print("FAILED.", "Respond Message: \n\n", parsed["respond"])
            return ""
        parsed = self.__getParsedData(path = path)
        # Traverse to the last next url in pagging. Will return [parsed, url]
        lastPagging = self.__lastNextPagging(parsed)
        url = lastPagging[1]
        parsed = lastPagging[0]
      
        # Get the "since" param in the url and use that for getting likes
        f = furl(url)
        TARGET_TIME = f.args["since"]
        # Get the last values[x]
        values = parsed["data"][0]["values"][len(parsed["data"][0]["values"])-1]
        #sort dictionary(value)
        value = dict(sorted(values["value"].items(), key=lambda item: item[1], reverse=True))
        #convert list of dict to list of list
        keys = list(value.keys()) 
        values = list(value.values())
        percentage = [None] * len(values)

        likes = self.__getTotalFan()
        for x in progressRep(range(len(values)),desc="Page Fans and Gender"):
            percentage[x] = values[x]/likes
 


        self.__ageGender = [keys,values,percentage]
        #DEBUG:
        # print(self.__AgeGender)
        # total_p = 0
        # for x in range(len(values)):
        #     total_p = total_p + percentage[x]
        # print(total_p)

        # Load self.__gender 
        
        male = []
        female = []
        undefined = []
        result = 0

        # Loop for M
        for x in range(len(keys)):
            if(re.match("M", keys[x])):
                male.append(values[x])
        for x in range(len(male)):
            result = result + male[x]
        male = result
        result = 0
        # Loop for F
        for x in range(len(keys)):
            if(re.match("F", keys[x])):
                female.append(values[x])
        for x in range(len(female)):
            result = result + female[x]
        female = result
        result = 0
        # Loop for U
        for x in range(len(keys)):
            if(re.match("U", keys[x])):
                undefined.append(values[x])
        for x in range(len(undefined)):
            result = result + undefined[x]
        undefined = result
        result = 0
        
        self.__gender = [male, female,undefined]
        





    #  Get number of times any content entered a person's screen
    # FB: The number of times any content from your Page or about your Page entered a person's screen. This includes posts, stories, ads, as well other content or information on your Page. (Total Count)
    def __getPageImpression(self):
        path = "insights?metric=page_impressions&period=day"
        value = [None] * 30
        timestamp = [None] * 30
        parsed = self.__getParsedData(path = path)
        # Traverse to the last next url in pagging. Will return [parsed, url]
        lastPagging = self.__lastNextPagging(parsed)
        url = lastPagging[1]
        parsed = lastPagging[0]
    
        #manipulate URL param (Revert param[since] back 30 days)
        f = furl(url)
        f.args["since"] = int(f.args["since"]) - (86400*30)

        # getParsedData for the new url with modified "since" parameter
        parsed = self.__getParsedData(url = f)
        # Assign to list
        for x in progressRep(range(0,30),desc="Page Impression"):
            value[x] = parsed["data"][0]["values"][x]["value"]
            #convert timestamps for display
            time = parsed["data"][0]["values"][x]["end_time"]
            time = time[0:10]
            date = datetime.strptime(time,'%Y-%m-%d')
            date = date.strftime("%b-%d")
            timestamp[x] = date

        self.__pageImpression = [timestamp,value] 
         # DEBUG:
        # print(self.__pageImpression)


    def __getTotalPageViews(self):
        path = "insights?metric=page_views_total&period=day"
        value = [None] * 30
        timestamp = [None] * 30
        parsed = self.__getParsedData(path = path)
        # Traverse to the last next url in pagging. Will return [parsed, url]
        lastPagging = self.__lastNextPagging(parsed)
        url = lastPagging[1]
        parsed = lastPagging[0]
    
        #manipulate URL param (Revert param[since] back 30 days)
        f = furl(url)
        f.args["since"] = int(f.args["since"]) - (86400*30)

        # getParsedData for the new url with modified "since" parameter
        parsed = self.__getParsedData(url = f)
        # Assign to list
        for x in progressRep(range(0,30),desc="Page Views"):
            value[x] = parsed["data"][0]["values"][x]["value"]
            #convert timestamps for display
            time = parsed["data"][0]["values"][x]["end_time"]
            time = time[0:10]
            date = datetime.strptime(time,'%Y-%m-%d')
            date = date.strftime("%b-%d")
            timestamp[x] = date

        self.__pageViews = [timestamp,value]
         # DEBUG:
        # print(self.__pageViews)



    def getDemographics(self):
        if(self.__ALLOW is False):
            print("Warning you can't access demographics data since your page has less than 100 page likes")
            return False
  
        self.__getCity()
        self.__getFansAddnRemove()
        self.__getPageFansGender()
        self.__getPageImpression()
        self.__getTotalPageViews()
        return { "demographics":{
            "city" : self.__city,
            "lat_long" : [self.__lat, self.__long],
            "new_likes" :self.__newLikes,
            "new_removed" : self.__newRemovedLikes,
            "gender_age":self.__ageGender,
            "gender" :  self.__gender,
            "page_impression":self.__pageImpression,
            "page_views":self.__pageViews
        }
         }
        


                
### BELOW CODES ARE USE FOR DEBUG PURPOSE ONLY!:
##### SHOULD NOT EXIST WHEN PRODUCTION!



# pg = PostsGrabber(token=token)
# pg.execute(3)

# dm = PageDemographic(token=token)
# data = dm.getDemographics()
# print(json.dumps(data, indent=4))
            
# token = 'INSERT_REAL_ACCESS_OR_LONG_LIVED_TOKEN_HERE'

# object = PageDemographic(token)
# object.getCity()


