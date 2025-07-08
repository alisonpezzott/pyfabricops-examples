# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }
# META   }
# META }

# MARKDOWN ********************

# ## Parameters

# CELL ********************

workspace_name = "01_fabric_simple-PRD"
lakehouse_name = "Lakehouse001"
lakehouse_abfss = f"abfss://{workspace_name}@onelake.dfs.fabric.microsoft.com/{lakehouse_name}.Lakehouse"
files_path = f"{lakehouse_abfss}/Files/Raw"
tables_path = f"{lakehouse_abfss}/Tables" 


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Imports

# CELL ********************

spark.conf.set('spark.sql.caseSensitive', True)
from pyspark.sql.functions import *

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## FactInternetSales

# CELL ********************

# Read
sales_path = f"{files_path}/dbo.FactInternetSales.parquet"
df_sales = spark.read.load(sales_path, format="parquet")
# display(df_sales) 

# Select columns
df_sales = df_sales.select(
    'ProductKey', 
    'OrderDateKey', 
    'DueDateKey', 
    'ShipDateKey', 
    'CustomerKey', 
    'SalesOrderNumber', 
    'OrderQuantity', 
    'UnitPrice', 
    'UnitPriceDiscountPct', 
    'ProductStandardCost'
)
# display(df_sales) 

# Write to tables
df_sales.write.format("delta") \
          .mode("overwrite") \
          .save(f"{tables_path}/FactInternetSales") 


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DimCustomer

# CELL ********************

# Read
customer_path = f"{files_path}/dbo.DimCustomer.parquet"
df_customer = spark.read.load(customer_path, format="parquet")
# display(df_customer)

# Select
df_customer = df_customer.select(
    "CustomerKey",
    "GeographyKey",
    "CustomerAlternateKey",
    "FirstName",
    "MiddleName",
    "LastName",
    "BirthDate",
    "Gender",
    "MaritalStatus",
    "TotalChildren",
    "EnglishEducation",
    "EnglishOccupation",
    "HouseOwnerFlag",
    "NumberCarsOwned"
)
# display(df_customer)

# Clean
df_customer = df_customer \
    .withColumn("FullName", concat_ws(" ", col("FirstName"), col("MiddleName"), col("LastName"))) \
    .drop("FirstName", "MiddleName", "LastName") \
    .withColumnsRenamed({
        "EnglishEducation":"Education",
        "EnglishOccupation": "Occupation"
    })
# display(df_customer) 

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Read Geography to join with Customers
geography_path = f"{files_path}/dbo.DimGeography.parquet"
df_geography = spark.read.load(geography_path, format="parquet")
# display(df_geography)

# Select
df_geography = df_geography.select(
    "GeographyKey", 
    "City",
    "EnglishCountryRegionName"
)
# display(df_geography)

# Clean
df_geography = df_geography \
    .withColumnRenamed("EnglishCountryRegionName", "CountryRegion") 
# display(df_geography)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Join Geography on Customer
df_customer = df_customer.join(
    df_geography,
    on="GeographyKey",  
    how="left"          
).drop("GeographyKey") 
# display(df_customer) 

# Write to tables
df_customer.write.format("delta") \
          .mode("overwrite") \
          .save(f"{tables_path}/DimCustomer")  

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DimProduct

# CELL ********************

# Read
product_path = f"{files_path}/dbo.DimProduct.parquet"
df_product = spark.read.load(product_path, format="parquet")
# display(df_product)

# Select
df_product = df_product.select(
    "ProductKey", 
    "ProductSubcategoryKey",
    "EnglishProductName",
    "Color",
    "Size",
    "ModelName",
    "LargePhoto",
    "EnglishDescription"
)
# display(df_product) 

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Read Category
product_category_path = f"{files_path}/dbo.DimProductCategory.parquet"
df_product_category = spark.read.load(product_category_path, format="parquet")
# display(df_product_category)

# Select
df_product_category = df_product_category.select(
    "ProductCategoryKey",
    "EnglishProductCategoryName"
)
# display(df_product_category) 

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Read Subcategory
product_subcategory_path = f"{files_path}/dbo.DimProductSubcategory.parquet"
df_product_subcategory = spark.read.load(product_subcategory_path, format="parquet")
# display(df_product_subcategory)

# Select
df_product_subcategory = df_product_subcategory.select("ProductSubcategoryKey", "EnglishProductSubcategoryName", "ProductCategoryKey") 
# display(df_product_subcategory) 

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Join subcategory on products
df_product = df_product.join(
    df_product_subcategory,
    on="ProductSubcategoryKey",
    how="left"
).drop("ProductSubcategoryKey")
# display(df_product)

# Join category on products
df_product = df_product.join(
    df_product_category,
    on="ProductCategoryKey",
    how="left"
).drop("ProductCategoryKey")
# display(df_product)

# Clean
df_product = df_product \
    .withColumnsRenamed(
        {
            "EnglishProductName" : "ProductName",
            "EnglishDescription": "Description",
            "EnglishProductSubcategoryName": "ProductSubcategoyName",
            "EnglishProductCategoryName": "ProductCategoryName" 
        }
    )
# display(df_product) 

# Write
df_product.write.format("delta") \
          .mode("overwrite") \
          .save(f"{tables_path}/DimProduct")   

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DimDate

# CELL ********************

# Read
date_path = f"{files_path}/dbo.DimDate.parquet"
df_date = spark.read.load(date_path, format="parquet")
# display(df_date)

# Select
df_date = df_date.drop("SpanishDayNameOfWeek", "FrenchDayNameOfWeek", "SpanishMonthName", "FrenchMonthName")
# display(df_date)

# Clean
df_date = df_date.withColumnsRenamed({"EnglishDayNameOfWeek":"DayNameOfWeek", "EnglishMonthName": "MonthName"})
# display(df_date) 

# Write
df_date.write.format("delta") \
          .mode("overwrite") \
          .save(f"{tables_path}/DimDate")   

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
