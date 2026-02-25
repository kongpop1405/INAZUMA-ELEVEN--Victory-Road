import json
import os
import time
from config import STATS_FILE

class StatsManager:
    def __init__(self):
        self.stats_file = STATS_FILE
        self.data = self._load_stats()

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"steps_data": {}, "total_rounds": 0}

    def update_stats(self, label, elapsed_time=0, is_round_end=False, is_step_back=False):
        if label not in self.data["steps_data"]: 
            self.data["steps_data"][label] = {"latencies": [], "total_searches": 0, "fail_count": 0, "success_count": 0, "step_back_count": 0}
        
        entry = self.data["steps_data"][label]
        if is_step_back:
            entry["step_back_count"] += 1
        else:
            if is_round_end: self.data["total_rounds"] += 1
            entry["success_count"] += 1
            entry["total_searches"] += 1
            if 0.01 <= elapsed_time < 30:
                lats = entry.get("latencies", [])
                lats.append(round(elapsed_time, 2))
                if len(lats) > 10: lats.pop(0)
                avg = round(sum(lats)/len(lats), 2)
                entry["avg_latency"] = avg
                entry["current_optimized_delay"] = max(0.1, round(avg * 1.1, 2))

        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        return entry.get("current_optimized_delay", 0.2), self.data["total_rounds"]