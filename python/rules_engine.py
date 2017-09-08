#This file will contain the python class used to check LAR data using the edits as described in the HMDA FIG
#This class should be able to return a list of row fail counts for each S/V edit for each file passed to the class.
#The return should be JSON formatted data, written to a file?
#input to the class will be a pandas dataframe
from io import StringIO
import pandas as pd

class rules_engine(object):
	"""docstring for ClassName"""
	def __init__(self, lar_schema, ts_schema, path="../edits_files/", data_file="passes_all.txt"):
		#lar and TS field names (load from schema names?)
		self.lar_field_names = list(lar_schema.field)
		self.ts_field_names = list(ts_schema.field)
		self.ts_df, self.lar_df= self.split_ts_row(path=path, data_file=data_file)
		self.results = {}
	#Helper Functions
	def split_ts_row(self, path="../edits_files/", data_file="passes_all.txt"):
		"""This function makes a separate data frame for the TS and LAR portions of a file and returns each as a dataframe."""
		with open(path+data_file, 'r') as infile:
			ts_row = infile.readline().strip("\n")
			ts_data = []
			ts_data.append(ts_row.split("|"))
			lar_rows = infile.readlines()
			lar_data = [line.strip("\n").split("|") for line in lar_rows]
			ts_df = pd.DataFrame(data=ts_data, dtype=object, columns=self.ts_field_names)
			lar_df  = pd.DataFrame(data=lar_data, dtype=object, columns=self.lar_field_names)
		return ts_df, lar_df

	#Edit Rules from FIG
	def s300(self):
		"""1) The first row of your file must begin with a 1; and 2) Any subsequent rows must begin with a 2."""
		self.results["s300"] = {}  #create s300 section of results
		self.results["s300"]["lar_fail_ids"] = [] #create list for failed row ids
		self.results["s300"]["ts_row"] = ""
		if self.ts_df.get_value(0,"record_id") != "1":
			self.results["s300"]["ts_row"] ="failed"
		else:
			self.results["s300"]["ts_row"] ="passed"
		count = 0 #initialize count of fail rows
		for index, row in self.lar_df.iterrows():
			if self.lar_df.get_value(index, "record_id")!="2":
				count+=1
				self.results["s300"]["lar_fail_ids"].append(self.lar_df.get_value(index, "uli"))
		self.results["s300"]["lar_fail_count"] = count


	def s301(self):
		"""The LEI in this row does not match the reported LEI in the transmittal sheet (the first row of your file). Please update your file accordingly."""
		self.results["s301"] = {}
		self.results["s301"]["lar_fail_ids"] = []
		ts_lei = self.ts_df.get_value(0, "lei")
		count = 0
		for index, row in self.lar_df.iterrows():
			if self.lar_df.get_value(index, "lei") != ts_lei:
				count+=1
				self.results["s301"]["lar_fail_ids"].append(self.lar_df.get_value(index, "lei"))
		self.results["s301"]["lar_fail_count"] = count


	def v600(self):
		"""1) The required format for LEI is alphanumeric with 20 characters, and it cannot be left blank."""
		self.results["v600"] = {}
		self.results["v600"]["lar_fail_ids"] = []
		#check LAR rows for LEI issues
		count = 0 #initialize fail count
		for index, row in self.lar_df.iterrows():
			if self.lar_df.get_value(index, "lei") == "" or len(self.lar_df.get_value(index, "lei"))!=20:
				count +=1
				self.results["v600"]["lar_fail_ids"].append(self.lar_df.get_value(index, "lei")) #append failed LEI value to list of fails
		self.results["v600"]["lar_fail_count"] = count #add count of fails to result

	def s302(self, year="2018"):
		""" The reported Calendar Year does not match the filing year indicated at the start of the filing."""
		#this applies to the TS only
		self.results["s302"] = {}
		self.results["s302"]["ts_row"] = ""
		
		if self.ts_df.get_value(0, "calendar_year") !=year:
			self.results["s302"]["ts_row"] = "failed"
		else:
			self.results["s302"]["ts_row"] = "passed"
	
	def s303(self):
		"""The reported Federal Agency; Federal Taxpayer Identification Number; and Legal Entity Identifier must match the Federal Agency;
		Federal Taxpayer Identification Number; and Legal Entity Identifier for the financial institution for which you are filing. """
		#checks against panel?
		#agency
		#tax ID
		#lei
		pass

	"""S304 The reported Total Number of Entries Contained in Submission does not match the total number of LARs in the HMDA file. Please update your file accordingly.
	
	V601 The following data fields are required, and cannot be left blank. A blank value(s) was provided. Please review the information below and update your file accordingly.
	1) Financial Institution Name;
	2) Contact Person's Name;
	3) Contact Person's E-mail Address;
	4) Contact Person's Office Street Address;
	5) Contact Person's Office City
	
	V602 An invalid Calendar Quarter was reported. Please review the information below and update your file accordingly.
	1) Calendar Quarter must equal 4, and cannot be left blank.

	V603 An invalid Contact Person's Telephone Number was provided. Please review the information below and update your file accordingly.
	1) The required format for the Contact Person's Telephone Number is 999-999-9999, and it cannot be left blank.
	
	V604 An invalid Contact Person's Office State was provided. Please review the information below and update your file accordingly.
	1) Contact Person's Office State must be a two letter state code, and cannot be left blank.
	
	V605 An invalid Contact Person's ZIP Code was provided. Please review the information below and update your file accordingly.
	1) The required format for the Contact Person's ZIP Code is 12345-1010 or 12345, and it cannot be left blank.
	
	V606 The reported Total Number of Entries Contained in Submission is not in the valid format. Please review the information below and update your file accordingly.
	1) The required format for the Total Number of Entries Contained in Submission is a whole number that is greater than zero, and it cannot be left blank.
	
	V607 An invalid Federal Taxpayer Identification Number was provided. Please review the information below and update your file accordingly.
	1) The required format for the Federal Taxpayer Identification Number is 99-9999999, and it cannot be left blank.
	
	S305 A duplicate transaction has been reported. Please review and update your file accordingly.
	
	V608 A ULI with an invalid format was provided. Please review the information below and update your file accordingly.
	1) The required format for ULI is alphanumeric with at least 23 characters and up to 45 characters, and it cannot be left blank.
	
	V609 An invalid ULI was reported. Please review the information below and update your file accordingly.
	1) Based on the check digit calculation, the ULI contains a transcription error.

	V610 An invalid data field was reported. Please review the information below and update your file accordingly.
	1) Application Date must be either a valid date using YYYYMMDD format or NA, and cannot be left blank.
	2) If Action Taken equals 6, then Application Date must be NA, and the reverse must be true.

	V611 An invalid Loan Type was reported. Please review the information below and update your file accordingly.
	1) Loan Type must equal 1, 2, 3, or 4, and cannot be left blank.

	V612 An invalid Loan Purpose was reported. Please review the information below and update your file accordingly.
	1) Loan Purpose must equal 1, 2, 31, 32, 4, or 5 and cannot be left blank.
	2) If Preapproval equals 1, then Loan Purpose must equal 1.

	V613 An invalid Preapproval data field was provided. Please review the information below and update your file accordingly.
	1) Preapproval must equal 1 or 2, and cannot be left blank.
	2) If Action Taken equals 7 or 8, then Preapproval must equal 1.
	3) If Action Taken equals 3, 4, 5 or 6, then Preapproval must equal 2.
	4) If Preapproval equals 1, then Action Taken must equal 1, 2, 7 or 8.

	V614 An invalid Preapproval was provided. Please review the information below and update your file accordingly.
	1) If Loan Purpose equals 2, 4, 31, 32, or 5, then Preapproval must equal 2.
	2) If Multifamily Affordable Units is a number, then Preapproval must equal 2.
	3) If Reverse Mortgage equals 1, then Preapproval must equal 2.
	4) If Open-End Line of Credit equals 1, then Preapproval must equal 2.

	V615 An invalid Construction Method was reported. Please review the information below and update your file accordingly.
	1) Construction Method must equal 1 or 2, and cannot be left blank.
	2) If Manufactured Home Land Property Interest equals 1, 2, 3 or 4, then Construction Method must equal 2.
	3) If Manufactured Home Secured Property Type equals 1 or 2 then Construction Method must equal 2.
	"""