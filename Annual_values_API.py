'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Yubai Liu
Student ID: z5143109

'''
import sqlite3
from sqlite3 import Error
import json
import requests
import datetime
from flask import Flask
from flask import request
from flask_restplus import Resource, Api
from flask_restplus import fields
from flask_restplus import inputs
from flask_restplus import reqparse
from operator import itemgetter


'''
database implement and it's functions
'''
# Create db
def create_db(db_file):
	try:
		conn = sqlite3.connect(db_file, check_same_thread=False)
		return conn
	except Error as e:
		print(e)

	return None

def insert_table(conn):
	if conn is not None:
		sql_create_collections_table = """ CREATE TABLE IF NOT EXISTS collections (
                                       	id integer PRIMARY KEY,
                                        indicator text NOT NULL,
                                        indicator_value text NOT NULL,
                                        creation_time text NOT NULL
                                    ); """
 
		sql_create_entries_table = """ CREATE TABLE IF NOT EXISTS entries (
									id integer PRIMARY KEY,
									country char(200),
									date text,
									value real,
									collection_id integer NOT NULL,
                                    FOREIGN KEY (collection_id) REFERENCES collections (id)
                                );"""
		create_table(conn, sql_create_collections_table)
		create_table(conn, sql_create_entries_table)

# create a new table 
def create_table(conn, create_table_sql):
	try:
		c = conn.cursor()
		c.execute(create_table_sql)
	except Error as e:
		print(e)

def insert_row(conn, row, table):
	sql_insert_collections = ''' INSERT INTO collections(indicator,indicator_value,creation_time)
             				 VALUES(?,?,?) '''

	sql_insert_entries = ''' INSERT INTO entries(country,date,value,collection_id)
							 VALUES(?,?,?,?) '''

	cur = conn.cursor()
	if table == 'collections':
		cur.execute(sql_insert_collections, row)
		return cur.lastrowid
	else:
		cur.execute(sql_insert_entries, row)

def select_by_column(conn, table, colunm):
    cur = conn.cursor()
    cur.execute(f"SELECT {colunm} FROM {table}")
 
    rows = cur.fetchall()

    print(type(rows))
    
    for row in rows:
    	print(row)

def select_all(conn, table):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
 
    rows = cur.fetchall()

    return rows

def select_by_condition(conn, table, condition):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} where {condition}")
    rows = cur.fetchall()
    return rows


def delete_by_condition(conn, table, condition):
	cur = conn.cursor()
	cur.execute(f"DELETE FROM {table} where {condition}")

def check_exist(collections):
	if len(collections) > 0:
		return 1
	else:
		return 0
'''
API REST part
'''
app = Flask(__name__)
api = Api(app, default='WorldBank', title='WorldBank Dataset', description='.')
indicator_model = api.model('Indicator',{'indicator_id' : fields.String('NY.GDP.MKTP.CD')})

@api.route('/collections')
class Collections(Resource):
	@api.response(200, 'Get collections Successfully')
	@api.response(400, 'Validation Error')
	@api.doc(description="Get all colletions")
	def get(self):
		collections = select_all(conn, 'collections')
		# check exist
		if len(collections) == 0:
			return {"message": "No data found, please POST first."}, 400
		response_list =	[]
		for collection in collections:
			response =	{}
			response['location'] =  f"/collections/{collection[0]}"
			response['collection_id'] = collection[0]
			response['creation_time'] = collection[3]
			response['indicator'] = collection[1]
			response_list.append(response)
		return response_list, 200

	@api.response(201, 'Collection imported Successfully')
	@api.response(200, 'Collection is already exist')
	@api.response(400, 'Validation Error')
	@api.doc(description="Import a new collection")
	@api.expect(indicator_model, validate = True)
	def post(self):
		global conn
		indicator = api.payload['indicator_id']
		# check if the an input contains a indicator that already exist
		collections = select_by_condition(conn, 'collections', f'indicator = "{indicator}"')
		if check_exist(collections) == 1: # the collection of given indicator is already exist
			# there should be only one tuple in the list of collections
			collection = collections[0]
			response =	{}
			response['location'] =  f"/collections/{collection[0]}"
			response['collection_id'] = collection[0]
			response['creation_time'] = collection[3]
			response['indicator'] = collection[1]
			return response, 200
		else: # the collection of given indicator is not exist
			# get data from url
			url_page1 = f'http://api.worldbank.org/v2/countries/all/indicators/{indicator}?date=2013:2018&format=json&page=1'
			url_page2 = f'http://api.worldbank.org/v2/countries/all/indicators/{indicator}?date=2013:2018&format=json&page=2'

			data1 = requests.get(url=url_page1)
			data1.encoding = "utf-8"
			parsed_data1 = data1.json()
			# check the given url is valid
			if len(parsed_data1) == 1:
				return {"message": "input indicator id does not exist"}, 404
			# data[0] is metadata
			parsed_data1 = parsed_data1[1]

			data2 = requests.get(url=url_page2)
			data2.encoding = "utf-8"
			parsed_data2 = data2.json()
			# data[0] is metadata
			parsed_data2 = parsed_data2[1]

			#compute total data
			parsed_data_total = parsed_data1 + parsed_data2
			
			# insert into database
			# insert collections table
			collection = (indicator, parsed_data_total[0]['indicator']['value'], str(datetime.datetime.now())[:-7])
			collection_id = insert_row(conn, collection, 'collections')

			# insert entries table
			for d in parsed_data_total:
				entry = (d['country']['value'], d['date'], d['value'], collection_id)
				insert_row(conn, entry, 'entries')

			# write response
			response =	{}
			response['location'] =  f"/collections/{collection_id}"
			response['collection_id'] = collection_id
			response['creation_time'] = str(datetime.datetime.now())[:-7]
			response['indicator'] = indicator

			return response, 201


@api.route('/collections/<int:collection_id>')
@api.param('collection_id', 'The collection_id which automatically generated when import the collection')
class Collection(Resource):
	@api.response(200, 'Get collection Successfully')
	@api.response(400, 'Validation Error')
	@api.doc(description="Get a collection")
	def get(self, collection_id):
		# check exist
		collections = select_by_condition(conn, 'collections', f'id = {collection_id}')
		if check_exist(collections) == 1:
			# there should be only one tuple in the list of collections
			collection = collections[0]
			response =	{}
			response['collection_id'] = collection[0]
			response['indicator'] = collection[1]
			response['indicator_value'] = collection[2]
			response['creation_time'] = collection[3]
			response['entries'] = []
			collection_entries = select_by_condition(conn, 'entries', f'collection_id = {collection_id}')
			# set entries 
			for entry in collection_entries:
				entry_output = {}
				entry_output['country'] = entry[1]
				entry_output['date'] = entry[2]
				entry_output['value'] = entry[3]
				response['entries'].append(entry_output)
			return response, 200
		else:
			return {"message": "No data found, the given collection is not exist."}, 400

	@api.response(200, 'Collection is Successfully deleted')
	@api.response(400, 'Validation Error')
	@api.doc(description="Delete a collection")
	def delete(self, collection_id):
		# check exist
		collections = select_by_condition(conn, 'collections', f'id = {collection_id}')
		if check_exist(collections) == 1:
			# delete collection from collections table
			delete_by_condition(conn, 'collections', f'id = {collection_id}')
			# delete all entry whose collection_id is given by user
			delete_by_condition(conn, 'entries', f'collection_id = {collection_id}')
			return {"message": f"Collection = {collection_id} is removed from the database!"}, 200
		else:
			return {"message": "No data found, the given collection is not exist."}, 400


@api.route('/collections/<int:collection_id>/<string:year>/<string:country>')
@api.response(200, 'Get data Successfully')
@api.response(400, 'Validation Error')
@api.doc(params={'collection_id':  'The collection_id which automatically generated when import the collection', 'year': 'Year between 2013 - 2018', 'country': ' Name of country you want to search'})
class CollectionYearCountry(Resource):
	def get(self, collection_id, year, country):
		# check valid year
		year_set = {'2013','2014','2015','2016','2017','2018'}
		if year not in year_set:
			return {"message": "Invalid year, The given year should be between 2013 and 2018"}, 400
		# check exist
		collections = select_by_condition(conn, 'collections', f'id = {collection_id}')
		if check_exist(collections) == 1:
			entries = select_by_condition(conn, 'entries', f'collection_id = {collection_id} and date = "{year}" and country = "{country}"')
			if check_exist(entries) == 1:
				# there should be only one tuple in the list of collections and entries
				collection = collections[0]
				entry = entries[0]
				response = {}
				response['collection_id'] = collection[0]
				response['indicator'] = collection[1]
				response['country'] = entry[1]
				response['year'] = entry[2]
				response['value'] = entry[3]
				return response, 200
			else:
				return {"message": "No data found for the given country and year."}, 400
		else:
			return {"message": "No data found, the given collection is not exist."}, 400

parser = reqparse.RequestParser()
parser.add_argument('query', type = str, help = 'top or bottom')
@api.route('/collections/<int:collection_id>/<string:year>')
@api.doc(params={'collection_id':  'The collection_id which automatically generated when import the collection', 'year': 'Year between 2013 - 2018'})
@api.response(200, 'Get data Successfully')
@api.response(400, 'Validation Error')
class TopBottom(Resource):

	@api.expect(parser, validate = True)
	def get(self, collection_id, year):
		query = parser.parse_args()['query']
		collections = select_by_condition(conn, 'collections', f'id = {collection_id}')
		if check_exist(collections) == 1:
			entries = select_by_condition(conn, 'entries', f'collection_id = {collection_id} and date = "{year}"')
			if check_exist(entries) == 1:
				# if no query specified
				if not query:
					collection = collections[0]
					response = {}
					response['indicator'] = collection[1]
					response['indicator_value'] = collection[2]
					response['entries'] = []
					for entry in entries:
						# check value is not null
						if entry[3] != None:
							entry_output = {}
							entry_output['country'] = entry[1]
							entry_output['date'] = entry[2]
							entry_output['value'] = entry[3]
							response['entries'].append(entry_output)
					response['entries'] = sorted(response['entries'], key = itemgetter('value'), reverse = True)
					return response, 200
				
				# top<N>
				elif 'top' in query and 'bottom' not in query:
					num = int(query[3:])
					if num < 1 or num > 100:
						return {"message": "Invalid query."}, 400
					collection = collections[0]
					response = {}
					response['indicator'] = collection[1]
					response['indicator_value'] = collection[2]
					response['entries'] = []
					for entry in entries:
						# check value is not null
						if entry[3] != None:
							entry_output = {}
							entry_output['country'] = entry[1]
							entry_output['date'] = entry[2]
							entry_output['value'] = entry[3]
							response['entries'].append(entry_output)
					response['entries'] = sorted(response['entries'], key = itemgetter('value'), reverse = True)
					if len(response['entries']) > num:
						response['entries'] = response['entries'][:num]
					return response, 200
					
				# bottom<N>
				elif 'bottom' in query and 'top' not in query:
					num = int(query[6:])
					if num < 1 or num > 100:
						return {"message": "Invalid query."}, 400
					collection = collections[0]
					response = {}
					response['indicator'] = collection[1]
					response['indicator_value'] = collection[2]
					response['entries'] = []
					for entry in entries:
						# check value is not null
						if entry[3] != None:
							entry_output = {}
							entry_output['country'] = entry[1]
							entry_output['date'] = entry[2]
							entry_output['value'] = entry[3]
							response['entries'].append(entry_output)
					response['entries'] = sorted(response['entries'], key = itemgetter('value'))
					if len(response['entries']) > num:
						response['entries'] = response['entries'][:num]
					return response, 200

				# invalid query
				else:
					return {"message": "Invalid query."},

			else:
				return {"message": "No data found for the given year, year shuold be between 2013 - 2018."}, 400
		else:
			return {"message": "No data found, the given collection is not exist."}, 400
		





# main function
if __name__ == '__main__':
	conn = create_db("WorldBank.db")
	insert_table(conn)
	app.run(debug=True)