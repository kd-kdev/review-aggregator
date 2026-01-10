import axios from "axios";

export function fetchGamesOverview() {
  return axios.get("/api/games/overview");
}
