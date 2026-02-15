export interface Scenario {
    id: string;
    name: string;
    description: string;
    topology_json: Topology;
    events_json: EventStream;
    yaml_content?: string;
    schema_version: string;
    created_at: string;
    updated_at: string;
}

export interface Topology {
    mermaid: string;
}

export interface EventStream {
    events: ScenarioEvent[];
}

export interface ScenarioEvent {
    kind: string;
    name: string;
    message: string;
}

export interface SimulationEvent {
    t: number;
    kind: string;
    actor?: string;
    target?: string;
    resource?: any;
    pod?: string;
    node?: string;
    reason?: string;
    details?: any;
    controller?: string;
}

export interface Session {
    id: string;
    title?: string;
    created_at: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    created_at: string;
}

export interface ChatResponse {
    message: Message;
    scenario_id?: string;
}
