
import React, { useEffect, useRef } from 'react';

export interface LogEntry {
    timestamp: string;
    component: string;
    kind: string;
    message: string;
    object: {
        kind: string;
        name: string;
    };
}

interface EventLogProps {
    logs: LogEntry[];
}

// Simple icons as text if lucide-react is not fully set up or to keep it simple first
const getIcon = (component: string) => {
    switch (component) {
        case 'Scheduler': return '🕒';
        case 'API Server': return '🖥️';
        case 'Kubelet': return '📦';
        case 'Controller': return '⚙️';
        default: return '📝';
    }
};

const EventLog: React.FC<EventLogProps> = ({ logs }) => {
    const endRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    return (
        <div className="event-log-container" style={{
            width: '300px',
            backgroundColor: '#1e1e1e',
            color: '#d4d4d4',
            borderLeft: '1px solid #333',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            overflow: 'hidden'
        }}>
            <div style={{
                padding: '10px',
                borderBottom: '1px solid #333',
                fontWeight: 'bold',
                display: 'flex',
                justifyContent: 'space-between',
                backgroundColor: '#252526'
            }}>
                <span>Cluster Events</span>
                <span style={{ fontSize: '0.8em', backgroundColor: '#333', padding: '2px 6px', borderRadius: '4px' }}>
                    {logs.length}
                </span>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
                {logs.length === 0 ? (
                    <div style={{ color: '#666', textAlign: 'center', marginTop: '20px', fontStyle: 'italic' }}>
                        No events yet...
                    </div>
                ) : (
                    logs.map((log, i) => (
                        <div key={i} style={{
                            marginBottom: '10px',
                            padding: '8px',
                            backgroundColor: '#2d2d2d',
                            borderRadius: '4px',
                            border: '1px solid #3e3e3e',
                            fontSize: '0.85rem'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                                <span style={{ marginRight: '8px' }}>{getIcon(log.component)}</span>
                                <span style={{ fontWeight: 'bold', color: '#9cdcfe' }}>{log.component}</span>
                                <span style={{ marginLeft: 'auto', fontSize: '0.7em', color: '#888' }}>
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                            <div style={{ paddingLeft: '24px' }}>
                                <div style={{ color: '#ce9178', marginBottom: '2px' }}>
                                    {log.kind}: {log.object.kind}/{log.object.name}
                                </div>
                                <div style={{ color: '#cccccc', lineHeight: '1.2' }}>
                                    {log.message}
                                </div>
                            </div>
                        </div>
                    ))
                )}
                <div ref={endRef} />
            </div>
        </div>
    );
};

export default EventLog;
