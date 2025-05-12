from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import struct
import random
from enum import Enum

class DNSRecordType(Enum):
    A = 1       # IPv4 address
    AAAA = 28   # IPv6 address
    CNAME = 5   # Canonical name
    MX = 15     # Mail exchange
    NS = 2      # Name server
    TXT = 16    # Text record

@dataclass
class DNSRecord:
    name: str
    record_type: DNSRecordType
    ttl: int
    data: str

@dataclass
class DNSQuery:
    transaction_id: int
    domain: str
    query_type: DNSRecordType
    recursion_desired: bool = True

    def serialize(self) -> bytes:
        # DNS header
        flags = 0x0100  # Standard query with recursion desired
        if self.recursion_desired:
            flags |= 0x0100

        header = struct.pack(
            '!HHHHHH',
            self.transaction_id,
            flags,
            1,  # Number of questions
            0,  # Answer RRs
            0,  # Authority RRs
            0   # Additional RRs
        )

        # Encode domain name
        question = b''
        for label in self.domain.split('.'):
            question += bytes([len(label)]) + label.encode('ascii')
        question += b'\x00'  # Root label

        # Query type and class
        question += struct.pack('!HH', self.query_type.value, 1)  # IN class

        return header + question

@dataclass
class DNSResponse:
    transaction_id: int
    answers: List[DNSRecord]
    authority: List[DNSRecord]
    additional: List[DNSRecord]

class DNSCache:
    def __init__(self):
        self.cache: Dict[Tuple[str, DNSRecordType], List[DNSRecord]] = {}
        self.negative_cache: Dict[Tuple[str, DNSRecordType], float] = {}

    def add(self, domain: str, record_type: DNSRecordType, records: List[DNSRecord]):
        key = (domain.lower(), record_type)
        self.cache[key] = records

    def get(self, domain: str, record_type: DNSRecordType) -> Optional[List[DNSRecord]]:
        key = (domain.lower(), record_type)
        return self.cache.get(key)

    def remove_expired(self):
        # In production, would check TTLs
        pass

class DNSResolver:
    def __init__(self):
        self.cache = DNSCache()
        self.root_servers = [
            "198.41.0.4",   # a.root-servers.net
            "199.9.14.201",  # b.root-servers.net
            "192.33.4.12",   # c.root-servers.net
        ]
        # Simulated DNS database
        self.records_db = self._init_records()

    def _init_records(self) -> Dict[str, List[DNSRecord]]:
        return {
            "example.com": [
                DNSRecord("example.com", DNSRecordType.A, 3600, "93.184.216.34"),
                DNSRecord("example.com", DNSRecordType.MX, 3600, "10 mail.example.com"),
                DNSRecord("example.com", DNSRecordType.NS, 86400, "ns1.example.com"),
            ],
            "www.example.com": [
                DNSRecord("www.example.com", DNSRecordType.CNAME, 3600, "example.com"),
            ],
            "mail.example.com": [
                DNSRecord("mail.example.com", DNSRecordType.A, 3600, "93.184.216.35"),
            ],
            "google.com": [
                DNSRecord("google.com", DNSRecordType.A, 300, "142.250.80.46"),
                DNSRecord("google.com", DNSRecordType.AAAA, 300, "2607:f8b0:4004:c07::71"),
            ],
        }

    def resolve(self, domain: str, record_type: DNSRecordType = DNSRecordType.A) -> Optional[List[DNSRecord]]:
        # Check cache first
        cached = self.cache.get(domain, record_type)
        if cached:
            return cached

        # Iterative resolution simulation
        records = self._lookup(domain, record_type)

        if records:
            self.cache.add(domain, record_type, records)

        return records

    def _lookup(self, domain: str, record_type: DNSRecordType) -> Optional[List[DNSRecord]]:
        # Simulate DNS lookup
        domain_records = self.records_db.get(domain, [])

        # Filter by record type
        matching_records = [
            r for r in domain_records if r.record_type == record_type
        ]

        # Handle CNAME redirection
        if not matching_records:
            cname_records = [
                r for r in domain_records if r.record_type == DNSRecordType.CNAME
            ]
            if cname_records:
                # Follow CNAME
                target = cname_records[0].data
                return self._lookup(target, record_type)

        return matching_records if matching_records else None

    def reverse_lookup(self, ip_address: str) -> Optional[str]:
        # PTR record lookup simulation
        for domain, records in self.records_db.items():
            for record in records:
                if record.record_type == DNSRecordType.A and record.data == ip_address:
                    return domain
        return None

class RecursiveDNSResolver(DNSResolver):
    def resolve_recursive(self, domain: str, record_type: DNSRecordType) -> Optional[List[DNSRecord]]:
        # Start from root servers
        current_servers = self.root_servers.copy()
        labels = domain.split('.')

        for i in range(len(labels) - 1, -1, -1):
            partial_domain = '.'.join(labels[i:])

            # Query current level servers
            ns_records = self._query_nameservers(current_servers, partial_domain, DNSRecordType.NS)

            if ns_records:
                # Move to next level nameservers
                current_servers = [r.data for r in ns_records]
            else:
                # Try to get final answer
                final_records = self._query_nameservers(current_servers, domain, record_type)
                if final_records:
                    return final_records

        return None

    def _query_nameserver(self, server: str, domain: str, record_type: DNSRecordType) -> Optional[List[DNSRecord]]:
        # Simulate nameserver query
        return self._lookup(domain, record_type)