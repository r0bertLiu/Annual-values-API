# Data-Service-for-world-bank
> This is a UNSW MIT project for course 9321

This project implemented a data service for a dataset provided by world bank. The datasetis Annual values of a user specified indicator from 2013 to 2018 for one or all countries. This project is realized by python Flask REST API and Sqlite3 database with some useful operation which help user to easily access the data.

## Operations:
The operation realized by this API are:

### 1- Import a collection to the data service:
Request:
```
HTTP operation: POST /<collections>
```
Response: 201 Created
```
{ 
    "location" : "/<collections>/<collection_id>", 
    "collection_id" : "<collection_id>",  
    "creation_time": "2019-03-09T12:06:11Z",
    "indicator" : "<indicator>"
}
```

### 2- Deleting a collection with the data service
Request:
```
HTTP operation: DELETE /<collections>/{collection_id}
```
Response: 200 OK
```
{ 
    "message" :"Collection = <collection_id> is removed from the database!"
}
```

### 3 - Retrieve the list of available collections
Request:
```
HTTP operation: GET /<collections>
```
Response: 200 OK
```
[
    "location" : "/<collections>/<collection_id_1>", 
    "collection_id" : "collection_id_1",  
    "creation_time": "<time>",
    "indicator" : "<indicator>"
    },
   { 
    "location" : "/<collections>/<collection_id_2>", 
    "collection_id" : "collection_id_2",  
    "creation_time": "<time>",
    "indicator" : "<indicator>"
   },
   ...
]
```

### 4 - Retrieve a collection
Request:
```
HTTP operation: GET /<collections>/{collection_id}
```
Response: 200 OK
```
{  
  "collection_id" : "<collection_id>",
  "indicator": "NY.GDP.MKTP.CD",
  "indicator_value": "GDP (current US$)",
  "creation_time" : "<creation_time>"
  "entries" : [
                {"country": "Arab World",  "date": "2016",  "value": 2513935702899.65 },
                {"country": "Caribbean small states",  "date": "2017",  "value": 68823642409.779 },
                ...
   ]
}
```

### 5 - Retrieve economic indicator value for given country and a year
Request:
```
HTTP operation: GET /<collections>/{collection_id}/{year}/{country}
```
Response: 200 OK
```
{ 
   "collection_id": <collection_id>,
   "indicator" : "<indicator_id>",
   "country": "<country>, 
   "year": "<year">,
   "value": <indicator_value_for_the_country>
}
```


### 6 - Retrieve top/bottom economic indicator values for a given year
Request:
```
HTTP operation: GET /<collections>/{collection_id}/{year}?q=<query>
```
Response: 200 OK
```
{ 
   "indicator": "NY.GDP.MKTP.CD",
   "indicator_value": "GDP (current US$)",
   "entries" : [
                  { 
                     "country": "Arab World",
                     "date": "2016",
                     "value": 2513935702899.65
                  },
                  ...
               ]
}
```

