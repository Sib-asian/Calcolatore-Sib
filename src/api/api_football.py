"""
API-Football Client for Live Match Statistics
https://www.api-football.com/documentation-v3

Provides real-time stats: shots, possession, corners, dangerous attacks, etc.
Free tier: 100 requests/day
"""

import os
import requests
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import json
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use existing environment


class APIFootballClient:
    """
    Client per API-Football (api-sports.io)
    Gestisce ricerca partite e statistiche live
    """

    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY", "")
        self.headers = {
            "x-apisports-key": self.api_key
        }
        self._cache = {}
        self._cache_duration = timedelta(minutes=2)  # Cache stats for 2 minutes

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Execute API request with error handling"""
        if not self.api_key:
            return {"error": "API key not configured"}

        try:
            import warnings
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')

            url = f"{self.BASE_URL}/{endpoint}"

            # Try request with retry logic
            response = None
            last_error = None

            for attempt in range(3):
                try:
                    # Try without SSL verification first (some environments have cert issues)
                    response = requests.get(
                        url,
                        headers=self.headers,
                        params=params,
                        timeout=15,
                        verify=False
                    )

                    # If we get 503 due to SSL issues, it won't raise exception
                    # So we check status code
                    if response.status_code == 200:
                        break
                    elif response.status_code == 503 and attempt < 2:
                        import time
                        time.sleep(1)
                        continue
                    else:
                        break

                except requests.exceptions.Timeout:
                    last_error = "Timeout"
                    if attempt < 2:
                        import time
                        time.sleep(1)
                        continue
                    raise
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    if attempt < 2:
                        import time
                        time.sleep(1)
                        continue
                    raise

            if response is None:
                return {"error": last_error or "No response"}

            if response.status_code == 200:
                data = response.json()
                # Check API-Football error format
                if data.get("errors") and len(data["errors"]) > 0:
                    return {"error": str(data["errors"])}
                return data
            elif response.status_code == 429:
                return {"error": "Rate limit exceeded (100/day)"}
            else:
                return {"error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key"""
        return f"{endpoint}:{json.dumps(params, sort_keys=True)}"

    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached result if valid"""
        if key in self._cache:
            cached_time, data = self._cache[key]
            if datetime.now() - cached_time < self._cache_duration:
                return data
        return None

    def _set_cache(self, key: str, data: Dict):
        """Cache result"""
        self._cache[key] = (datetime.now(), data)

    def search_live_fixtures(self, team_name: str = None) -> List[Dict]:
        """
        Search for live fixtures

        Args:
            team_name: Optional team name to filter

        Returns:
            List of live fixtures
        """
        params = {"live": "all"}

        cache_key = self._get_cache_key("fixtures", params)
        cached = self._get_cached(cache_key)
        if cached:
            fixtures = cached.get("response", [])
        else:
            result = self._make_request("fixtures", params)
            if result and "error" not in result:
                self._set_cache(cache_key, result)
                fixtures = result.get("response", [])
            else:
                return []

        # Filter by team name if provided
        if team_name and fixtures:
            team_lower = team_name.lower()
            filtered = []
            for fix in fixtures:
                home = fix.get("teams", {}).get("home", {}).get("name", "").lower()
                away = fix.get("teams", {}).get("away", {}).get("name", "").lower()
                if team_lower in home or team_lower in away:
                    filtered.append(fix)
            return filtered

        return fixtures

    def find_fixture_by_teams(self, team_home: str, team_away: str) -> Optional[Dict]:
        """
        Find a specific live fixture by team names

        Args:
            team_home: Home team name
            team_away: Away team name

        Returns:
            Fixture data or None
        """
        fixtures = self.search_live_fixtures()

        if not fixtures:
            return None

        home_lower = team_home.lower()
        away_lower = team_away.lower()

        best_match = None
        best_score = 0

        for fix in fixtures:
            fix_home = fix.get("teams", {}).get("home", {}).get("name", "").lower()
            fix_away = fix.get("teams", {}).get("away", {}).get("name", "").lower()

            # Calculate match score
            score = 0
            if home_lower in fix_home or fix_home in home_lower:
                score += 1
            if away_lower in fix_away or fix_away in away_lower:
                score += 1

            # Exact match bonus
            if home_lower == fix_home:
                score += 2
            if away_lower == fix_away:
                score += 2

            if score > best_score:
                best_score = score
                best_match = fix

        # Require at least one team to match
        if best_score >= 1:
            return best_match

        return None

    def get_fixture_statistics(self, fixture_id: int) -> Optional[Dict]:
        """
        Get statistics for a specific fixture

        Args:
            fixture_id: The fixture ID

        Returns:
            Statistics data with both teams' stats
        """
        params = {"fixture": fixture_id}

        cache_key = self._get_cache_key("fixtures/statistics", params)
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        result = self._make_request("fixtures/statistics", params)

        if result and "error" not in result:
            self._set_cache(cache_key, result)
            return result

        return result

    def get_live_stats(self, team_home: str, team_away: str) -> Dict[str, Any]:
        """
        Get live statistics for a match by team names

        This is the main method to use from the UI.

        Args:
            team_home: Home team name
            team_away: Away team name

        Returns:
            Dict with normalized statistics:
            {
                'found': bool,
                'fixture_id': int,
                'match_info': {...},
                'stats': {
                    'home': {...},
                    'away': {...}
                },
                'normalized': {
                    'shots_total_home': int,
                    'shots_total_away': int,
                    'shots_on_target_home': int,
                    'shots_on_target_away': int,
                    'possession_home': int,
                    'possession_away': int,
                    'corners_home': int,
                    'corners_away': int,
                    'dangerous_attacks_home': int,
                    'dangerous_attacks_away': int,
                    ...
                },
                'error': str (if any)
            }
        """
        # Find the fixture
        fixture = self.find_fixture_by_teams(team_home, team_away)

        if not fixture:
            return {
                'found': False,
                'error': f"No live match found for {team_home} vs {team_away}"
            }

        fixture_id = fixture.get("fixture", {}).get("id")

        if not fixture_id:
            return {
                'found': False,
                'error': "Fixture ID not found"
            }

        # Get statistics
        stats_result = self.get_fixture_statistics(fixture_id)

        if not stats_result or "error" in stats_result:
            return {
                'found': True,
                'fixture_id': fixture_id,
                'match_info': self._extract_match_info(fixture),
                'stats': None,
                'normalized': None,
                'error': stats_result.get("error", "Failed to get statistics")
            }

        # Parse and normalize statistics
        stats_response = stats_result.get("response", [])

        if len(stats_response) < 2:
            return {
                'found': True,
                'fixture_id': fixture_id,
                'match_info': self._extract_match_info(fixture),
                'stats': None,
                'normalized': None,
                'error': "Incomplete statistics data"
            }

        # Parse stats for both teams
        home_stats = self._parse_team_stats(stats_response[0])
        away_stats = self._parse_team_stats(stats_response[1])

        # Create normalized structure
        normalized = self._normalize_stats(home_stats, away_stats)

        return {
            'found': True,
            'fixture_id': fixture_id,
            'match_info': self._extract_match_info(fixture),
            'stats': {
                'home': home_stats,
                'away': away_stats
            },
            'normalized': normalized,
            'error': None
        }

    def _extract_match_info(self, fixture: Dict) -> Dict:
        """Extract basic match info from fixture"""
        return {
            'home_team': fixture.get("teams", {}).get("home", {}).get("name", ""),
            'away_team': fixture.get("teams", {}).get("away", {}).get("name", ""),
            'home_logo': fixture.get("teams", {}).get("home", {}).get("logo", ""),
            'away_logo': fixture.get("teams", {}).get("away", {}).get("logo", ""),
            'score_home': fixture.get("goals", {}).get("home", 0),
            'score_away': fixture.get("goals", {}).get("away", 0),
            'minute': fixture.get("fixture", {}).get("status", {}).get("elapsed", 0),
            'status': fixture.get("fixture", {}).get("status", {}).get("short", ""),
            'league': fixture.get("league", {}).get("name", ""),
            'country': fixture.get("league", {}).get("country", "")
        }

    def _parse_team_stats(self, team_data: Dict) -> Dict:
        """Parse statistics for one team"""
        stats = {}
        statistics = team_data.get("statistics", [])

        for stat in statistics:
            stat_type = stat.get("type", "").lower().replace(" ", "_")
            value = stat.get("value")

            # Handle percentage values
            if isinstance(value, str) and "%" in value:
                value = int(value.replace("%", ""))
            elif value is None:
                value = 0

            stats[stat_type] = value

        return stats

    def _normalize_stats(self, home_stats: Dict, away_stats: Dict) -> Dict:
        """
        Create normalized statistics structure for easy use in calculations
        """
        def safe_int(val):
            """Safely convert to int"""
            if val is None:
                return 0
            if isinstance(val, str):
                try:
                    return int(val.replace("%", ""))
                except:
                    return 0
            return int(val)

        return {
            # Shots
            'shots_total_home': safe_int(home_stats.get('total_shots') or home_stats.get('shots_total', 0)),
            'shots_total_away': safe_int(away_stats.get('total_shots') or away_stats.get('shots_total', 0)),
            'shots_on_target_home': safe_int(home_stats.get('shots_on_goal') or home_stats.get('shots_on_target', 0)),
            'shots_on_target_away': safe_int(away_stats.get('shots_on_goal') or away_stats.get('shots_on_target', 0)),
            'shots_off_target_home': safe_int(home_stats.get('shots_off_goal') or home_stats.get('shots_off_target', 0)),
            'shots_off_target_away': safe_int(away_stats.get('shots_off_goal') or away_stats.get('shots_off_target', 0)),

            # Possession
            'possession_home': safe_int(home_stats.get('ball_possession', 50)),
            'possession_away': safe_int(away_stats.get('ball_possession', 50)),

            # Corners
            'corners_home': safe_int(home_stats.get('corner_kicks', 0)),
            'corners_away': safe_int(away_stats.get('corner_kicks', 0)),

            # Attacks
            'attacks_home': safe_int(home_stats.get('total_attacks', 0)),
            'attacks_away': safe_int(away_stats.get('total_attacks', 0)),
            'dangerous_attacks_home': safe_int(home_stats.get('dangerous_attacks', 0)),
            'dangerous_attacks_away': safe_int(away_stats.get('dangerous_attacks', 0)),

            # Fouls & Cards
            'fouls_home': safe_int(home_stats.get('fouls', 0)),
            'fouls_away': safe_int(away_stats.get('fouls', 0)),
            'yellow_cards_home': safe_int(home_stats.get('yellow_cards', 0)),
            'yellow_cards_away': safe_int(away_stats.get('yellow_cards', 0)),
            'red_cards_home': safe_int(home_stats.get('red_cards', 0)),
            'red_cards_away': safe_int(away_stats.get('red_cards', 0)),

            # Goalkeeper
            'saves_home': safe_int(home_stats.get('goalkeeper_saves', 0)),
            'saves_away': safe_int(away_stats.get('goalkeeper_saves', 0)),

            # Passing
            'passes_total_home': safe_int(home_stats.get('total_passes', 0)),
            'passes_total_away': safe_int(away_stats.get('total_passes', 0)),
            'passes_accurate_home': safe_int(home_stats.get('passes_accurate', 0)),
            'passes_accurate_away': safe_int(away_stats.get('passes_accurate', 0)),

            # Offsides
            'offsides_home': safe_int(home_stats.get('offsides', 0)),
            'offsides_away': safe_int(away_stats.get('offsides', 0)),
        }

    def calculate_stats_advantage(self, normalized_stats: Dict) -> Dict[str, float]:
        """
        Calculate advantage metrics from normalized stats

        Returns ratios where:
        - 0.5 = equal
        - > 0.5 = home advantage
        - < 0.5 = away advantage
        """
        def safe_ratio(home_val, away_val) -> float:
            """Calculate safe ratio (0.5 if both zero)"""
            total = home_val + away_val
            if total == 0:
                return 0.5
            return home_val / total

        stats = normalized_stats

        # Core metrics
        shots_ratio = safe_ratio(stats['shots_total_home'], stats['shots_total_away'])
        shots_target_ratio = safe_ratio(stats['shots_on_target_home'], stats['shots_on_target_away'])
        possession_ratio = stats['possession_home'] / 100.0
        corners_ratio = safe_ratio(stats['corners_home'], stats['corners_away'])
        dangerous_ratio = safe_ratio(stats['dangerous_attacks_home'], stats['dangerous_attacks_away'])

        # Weighted combined advantage
        # Weights: shots on target (40%), dangerous attacks (25%), possession (20%), corners (15%)
        combined_advantage = (
            shots_target_ratio * 0.40 +
            dangerous_ratio * 0.25 +
            possession_ratio * 0.20 +
            corners_ratio * 0.15
        )

        # Alternative: attack pressure metric
        attack_pressure = (
            shots_ratio * 0.35 +
            dangerous_ratio * 0.35 +
            corners_ratio * 0.30
        )

        return {
            'shots_ratio': round(shots_ratio, 3),
            'shots_on_target_ratio': round(shots_target_ratio, 3),
            'possession_ratio': round(possession_ratio, 3),
            'corners_ratio': round(corners_ratio, 3),
            'dangerous_attacks_ratio': round(dangerous_ratio, 3),
            'combined_advantage': round(combined_advantage, 3),
            'attack_pressure': round(attack_pressure, 3),
            # Interpretation
            'home_dominance': combined_advantage > 0.55,
            'away_dominance': combined_advantage < 0.45,
            'balanced': 0.45 <= combined_advantage <= 0.55
        }

    def check_api_status(self) -> Dict:
        """
        Check API status and remaining requests

        Returns:
            Dict with status info
        """
        result = self._make_request("status")

        if result and "error" not in result:
            response = result.get("response", {})
            return {
                'active': True,
                'account': response.get("account", {}).get("firstname", "Unknown"),
                'requests_today': response.get("requests", {}).get("current", 0),
                'requests_limit': response.get("requests", {}).get("limit_day", 100),
                'requests_remaining': response.get("requests", {}).get("limit_day", 100) - response.get("requests", {}).get("current", 0)
            }

        return {
            'active': False,
            'error': result.get("error", "Unknown error") if result else "No response"
        }


# Singleton instance for easy import
_client_instance = None

def get_api_football_client() -> APIFootballClient:
    """Get singleton instance of API Football client"""
    global _client_instance
    if _client_instance is None:
        _client_instance = APIFootballClient()
    return _client_instance
