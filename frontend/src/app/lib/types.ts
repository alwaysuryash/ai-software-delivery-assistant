export type Health = "green" | "amber" | "red" | "unknown";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  owner: string;
  status: string;
  current_health: Health;
}
