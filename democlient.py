import xmlrpc.client

ODOO_BACKEND = 'htp://localhost:8000'
ODOO_DB = 'demo2'
ODOO_USER = 'cons'
ODOO_PASS = 'saddas'

def myprint(data_list, title=''):
	if title:
		print(title)
	for line in data_list:
		print('-', line)
	pass

class XMLRPC_API():
	def __init__(self, url, db, username='cons', password='saddas'):
		self.url = url
		self.db = db
		self.username = username
		self.password = password
		common = xmlrpc.client.ServerProxy('%s/xmlrpc/2/common'%self.url)
		self.uid = common.authenticate(self.db, self.username, self.password, {})
		self.models = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object'%self.url)
		pass

	def get_fields(self, model_name, required=False):
		data = self.models.execute_kw(self.db, self.uid, self.password, model_name, 'fields_get', [], {'attributes': ['string', 'type', 'required', 'readonly']})
		
		if required:
			key_list = list(data.keys())
			for k in key_list:
				if not data[k].get('required', False):
					data.pop(k)
				pass
		return data
	def search(self, model_name, conditions=[()]):
		return self.models.execute_kw(self.db, self.uid, self.password, model_name, 'search', [conditions])

# Create
	def create(self, model_name, data_dict):
		id = self.models.execute_kw(self.db, self.uid, self.password, model_name, 'create', [data_dict])
		return id

    # Read
	def read(self, model_name, conditions=[()], params={}):
		return self.models.execute_kw(self.db, self.uid, self.password, model_name,'search_read', [conditions], params)       
    
    # Update
	def update(self, model_name, id_list, new_data_dict):
		self.models.execute_kw(self.db, self.uid, self.password, model_name,'write',[id_list, new_data_dict])

    # Delete
	def delete(self, model_name, id_list):
		self.models.execute_kw(self.db, self.uid, self.password, model_name, 'unlink', [id_list])
		pass

    # Soft delete
	def soft_delete(self, model_name, id_list):
		self.update(model_name, id_list, {'active': False,})

    # Aug 01, 2019
	def call(self, model_name, method, params=[]):
		return self.models.execute_kw(self.db, self.uid, self.password, model_name, method, params)

	def call2(self, model_name, method, param1, param2):
		return self.models.execute_kw(self.db, self.uid, self.password, model_name, method, param1, param2)

def main():
	client = XMLRPC_API(url=ODOO_BACKEND, db=ODOO_DB, username=ODOO_USER, password=ODOO_PASS)

    # list vendor accounts
	myprint(client.read(model_name='my.pot', conditions=[('id', '>=', 1)], params={ 'fields': ['name', 'nickname'], }), title='Read My Pet')
	myprint(client.call2(model_name="my.pot", method="search_read", param1=[[('id', '>=', 1)]], param2={}), title='General Call')

	client.create(model_name="my.pot", data_dict={"name": "Minh", "nickname": "Kyz"})
	print("Created new pot")

	client.update(model_name="my.pot", id_list=[1], new_data_dict={"name": "Kitte", "nickname": "Sugar Baby"})
	print("Update new pot")

	pass

if __name__ == '__main__':
	main()
