export type Route = {
  id: number;
  route_number: string;
  name: string;
  source: string;
  destination: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Bus = {
  id: number;
  registration_number: string;
  route_id: number | null;
  bus_type: string;
  operator_name: string | null;
  capacity: number | null;
  status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type BusLocation = {
  id: number;
  bus_id: number;
  latitude: string;
  longitude: string;
  speed_kmph: string | null;
  heading_degrees: number | null;
  recorded_at: string;
  received_at: string;
};

export type LocationSocketMessage = {
  type: 'location_update' | 'latest_location';
  data: BusLocation;
};

