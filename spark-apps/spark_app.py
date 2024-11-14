from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("KafkaToHudi") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .getOrCreate()

# Set Logging Level for Detailed Logs (Optional)
spark.sparkContext.setLogLevel("DEBUG")  # Adjust as needed

# Kafka Configuration
kafka_bootstrap_servers = "kafka:29092"  # Internal Docker network address
kafka_topic = "test_topic"

# Define Schema for Incoming Data
schema = StructType([
    StructField("record_key", StringType(), True),
    StructField("partition_path", StringType(), True),
    StructField("value", IntegerType(), True),
    StructField("timestamp", StringType(), True)  # Ensure this matches your data
])

# Read Streaming Data from Kafka
json_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "earliest") \
    .load() \
    .selectExpr("CAST(value AS STRING) as json_string") \
    .select(from_json(col("json_string"), schema).alias("data")) \
    .select("data.*") \
    .filter(col("record_key").isNotNull())  # Ensure record_key is not null

# Optional: Print Schema for Debugging
json_df.printSchema()

# Hudi Configuration
hudi_table_path = "/mnt/hudi-data/hudi_test_table"
checkpoint_location = "/mnt/hudi-data/checkpoints"

# Write Streaming Data to Hudi
hudi_write_query = json_df.writeStream \
    .format("org.apache.hudi") \
    .option("hoodie.datasource.write.recordkey.field", "record_key") \
    .option("hoodie.datasource.write.partitionpath.field", "partition_path") \
    .option("hoodie.table.name", "hudi_test_table") \
    .option("hoodie.datasource.write.operation", "upsert") \
    .option("hoodie.datasource.write.table.type", "COPY_ON_WRITE") \
    .option("hoodie.datasource.hive_sync.enable", "false") \
    .option("hoodie.datasource.write.precombine.field", "timestamp") \
    .option("hoodie.datasource.write.keygenerator.class", "org.apache.hudi.keygen.SimpleKeyGenerator") \
    .option("checkpointLocation", checkpoint_location) \
    .trigger(processingTime='10 seconds') \
    .start(hudi_table_path)

# Await Termination
hudi_write_query.awaitTermination()

