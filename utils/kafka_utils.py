"""
Kafka utility functions for the arbitrage betting project
"""
import json
import logging
from typing import List, Dict, Any
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

logger = logging.getLogger(__name__)

class KafkaUtils:
    """Utility class for Kafka operations"""
    
    @staticmethod
    def create_topics(bootstrap_servers: List[str], topics: List[str], 
                     num_partitions: int = 1, replication_factor: int = 1) -> bool:
        """Create Kafka topics if they don't exist"""
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
            
            topic_list = []
            for topic in topics:
                topic_list.append(NewTopic(
                    name=topic,
                    num_partitions=num_partitions,
                    replication_factor=replication_factor
                ))
            
            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            logger.info(f"Created topics: {topics}")
            return True
            
        except TopicAlreadyExistsError:
            logger.info(f"Topics already exist: {topics}")
            return True
        except Exception as e:
            logger.error(f"Failed to create topics: {e}")
            return False
    
    @staticmethod
    def get_producer(bootstrap_servers: List[str]) -> KafkaProducer:
        """Create a Kafka producer with JSON serialization"""
        return KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # Wait for all replicas to acknowledge
            retries=3,   # Retry failed sends
            batch_size=16384,  # Batch size in bytes
            linger_ms=10  # Wait time for batching
        )
    
    @staticmethod
    def get_consumer(bootstrap_servers: List[str], topics: List[str], 
                    group_id: str = "arbitrage_group") -> KafkaConsumer:
        """Create a Kafka consumer with JSON deserialization"""
        return KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest',  # Start from latest messages
            enable_auto_commit=True,     # Automatically commit offsets
            consumer_timeout_ms=1000     # Timeout for polling
        )
    
    @staticmethod
    def send_message(producer: KafkaProducer, topic: str, 
                    message: Dict[Any, Any], key: str = None) -> bool:
        """Send a message to Kafka topic"""
        try:
            future = producer.send(topic, value=message, key=key)
            producer.flush()  # Ensure message is sent
            logger.debug(f"Sent message to {topic}: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            return False
    
    @staticmethod
    def check_kafka_connection(bootstrap_servers: List[str]) -> bool:
        """Check if Kafka is reachable"""
        try:
            producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
            producer.close()
            logger.info("Kafka connection successful")
            return True
        except Exception as e:
            logger.error(f"Kafka connection failed: {e}")
            return False