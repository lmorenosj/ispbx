#!/usr/bin/env python3
# /home/ubuntu/Documents/ispbx/backend/tests/queue_mock_data.py

import json
import random
import argparse
from typing import Dict, List, Any

def generate_mock_queues(count: int = 5) -> List[Dict[str, Any]]:
    """Generate mock queue data"""
    strategies = ["ringall", "leastrecent", "fewestcalls", "random", "rrmemory", "linear", "wrandom"]
    queues = []
    
    for i in range(1, count + 1):
        queue_name = f"queue_{i}"
        strategy = random.choice(strategies)
        member_count = random.randint(0, 10)
        
        queue = {
            "name": queue_name,
            "strategy": strategy,
            "member_count": member_count
        }
        queues.append(queue)
    
    return queues

def generate_mock_queue_details(queue_name: str) -> Dict[str, Any]:
    """Generate mock queue details"""
    strategies = ["ringall", "leastrecent", "fewestcalls", "random", "rrmemory", "linear", "wrandom"]
    
    queue = {
        "queue": {
            "name": queue_name,
            "strategy": random.choice(strategies),
            "timeout": str(random.randint(10, 60)),
            "musiconhold": "default",
            "announce": "",
            "context": "from-queue",
            "maxlen": str(random.randint(0, 50)),
            "servicelevel": str(random.randint(30, 120)),
            "wrapuptime": str(random.randint(0, 30))
        },
        "status": {
            "calls": random.randint(0, 10),
            "completed": random.randint(0, 200),
            "abandoned": random.randint(0, 50),
            "holdtime": random.randint(0, 300),
            "talktime": random.randint(0, 600)
        }
    }
    
    return queue

def generate_mock_queue_members(queue_name: str, count: int = 5) -> List[Dict[str, Any]]:
    """Generate mock queue members"""
    statuses = ["Available", "In Use", "Busy", "Unavailable", "Ringing"]
    members = []
    
    for i in range(1, count + 1):
        extension = 1000 + i
        interface = f"PJSIP/{extension}"
        member_name = f"Agent {i}"
        penalty = random.randint(0, 5)
        paused = random.choice([True, False])
        status = random.choice(statuses)
        
        member = {
            "interface": interface,
            "membername": member_name,
            "penalty": str(penalty),
            "paused": paused,
            "status": status
        }
        members.append(member)
    
    return members

def generate_all_mock_data(queue_count: int = 5, member_max: int = 5) -> Dict[str, Any]:
    """Generate all mock data for queues, details, and members"""
    queues = generate_mock_queues(queue_count)
    all_data = {
        "queues": queues,
        "queue_details": {},
        "queue_members": {}
    }
    
    for queue in queues:
        queue_name = queue["name"]
        member_count = random.randint(0, member_max)
        
        all_data["queue_details"][queue_name] = generate_mock_queue_details(queue_name)
        all_data["queue_members"][queue_name] = generate_mock_queue_members(queue_name, member_count)
    
    return all_data

def main():
    parser = argparse.ArgumentParser(description="Generate mock data for queue testing")
    parser.add_argument("--queues", type=int, default=5, help="Number of queues to generate")
    parser.add_argument("--members", type=int, default=5, help="Maximum number of members per queue")
    parser.add_argument("--output", type=str, default="queue_mock_data.json", help="Output file name")
    parser.add_argument("--pretty", action="store_true", help="Pretty print the JSON output")
    args = parser.parse_args()
    
    mock_data = generate_all_mock_data(args.queues, args.members)
    
    indent = 2 if args.pretty else None
    with open(args.output, "w") as f:
        json.dump(mock_data, f, indent=indent)
    
    print(f"Generated mock data for {args.queues} queues and saved to {args.output}")

if __name__ == "__main__":
    main()
