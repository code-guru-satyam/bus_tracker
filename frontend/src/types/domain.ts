export type Route = {
  id: number;
  route_number: string;
  name: string;
  source: string;
  destination: string;
  description: string | null;
  stop_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type RouteStop = {
  id: number;
  route_id: number;
  stop_name: string;
  latitude: string;
  longitude: string;
  sequence_number: number;
  created_at: string;
  updated_at: string;
};

export type RouteStopCreate = {
  stop_name: string;
  latitude: string;
  longitude: string;
  sequence_number: number;
};

export type RouteStopUpdate = Partial<RouteStopCreate>;

export type RouteGeometry = {
  route_id: number;
  coordinates: Array<[number, number]>;
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

