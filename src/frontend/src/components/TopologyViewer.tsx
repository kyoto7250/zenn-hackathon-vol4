import { useEffect, useMemo, useState } from 'react';
import { getScenario, retryScenarioDiagram } from '../services/api';
import type { Scenario } from '../types';
import './TopologyViewer.css';

interface TopologyViewerProps {
    scenarioId: string;
}

type MermaidGlobal = {
    initialize: (config: Record<string, unknown>) => void;
    render: (id: string, code: string) => Promise<{ svg: string }>;
};

declare global {
    interface Window {
        mermaid?: MermaidGlobal;
    }
}

let mermaidScriptLoading: Promise<void> | null = null;

const sanitizeRenderError = (message: string): string => {
    const normalized = (message || '').trim();
    if (normalized.includes('Syntax error in text')) {
        return 'Syntax error in text';
    }
    return normalized;
};

const loadMermaid = async (): Promise<void> => {
    if (window.mermaid) {
        return;
    }

    if (!mermaidScriptLoading) {
        mermaidScriptLoading = new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js';
            script.async = true;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Failed to load Mermaid script.'));
            document.head.appendChild(script);
        });
    }

    await mermaidScriptLoading;
};

export default function TopologyViewer({ scenarioId }: TopologyViewerProps) {
    const [scenario, setScenario] = useState<Scenario | null>(null);
    const [diagramSvg, setDiagramSvg] = useState('');
    const [diagramError, setDiagramError] = useState<string | null>(null);
    const [renderErrorDetail, setRenderErrorDetail] = useState('');
    const [retryInstruction, setRetryInstruction] = useState('');
    const [retrying, setRetrying] = useState(false);
    const [retryError, setRetryError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'diagram' | 'scenario' | 'yaml'>('diagram');

    const mermaidText = useMemo(() => {
        return scenario?.topology_json?.mermaid ?? '';
    }, [scenario]);

    useEffect(() => {
        if (!scenarioId) return;
        getScenario(scenarioId).then(setScenario).catch(console.error);
    }, [scenarioId]);

    useEffect(() => {
        if (!mermaidText) {
            setDiagramSvg('');
            return;
        }

        let cancelled = false;

        const renderMermaid = async () => {
            try {
                await loadMermaid();
                const mermaid = window.mermaid;
                if (!mermaid) {
                    throw new Error('Mermaid is not available on window.');
                }

                mermaid.initialize({
                    startOnLoad: false,
                    securityLevel: 'loose',
                    theme: 'base',
                    themeVariables: {
                        darkMode: false,
                        background: '#FFFFFF',
                        primaryColor: '#FFFFFF',
                        primaryTextColor: '#111827',
                        primaryBorderColor: '#6B7280',
                        secondaryColor: '#FFFFFF',
                        tertiaryColor: '#ffffff',
                        lineColor: '#424242',
                        edgeLabelBackground: '#FFFFFF',
                        clusterBkg: '#FFFFFF',
                        clusterBorder: '#9CA3AF',
                        fontFamily: 'ui-sans-serif, system-ui'
                    }
                });

                const renderId = `mermaid-${scenarioId}-${Date.now()}`;
                const { svg } = await mermaid.render(renderId, mermaidText);
                if (!cancelled) {
                    setDiagramError(null);
                    setRenderErrorDetail('');
                    setRetryError(null);
                    setDiagramSvg(svg);
                }
            } catch (error) {
                console.error(error);
                if (!cancelled) {
                    setDiagramSvg('');
                    setDiagramError('Mermaid図の描画に失敗しました。');
                    const detail = error instanceof Error ? error.message : 'Unknown render error';
                    setRenderErrorDetail(sanitizeRenderError(detail));
                }
            }
        };

        renderMermaid();

        return () => {
            cancelled = true;
        };
    }, [mermaidText, scenarioId]);

    const handleRetryDiagram = async () => {
        if (!scenarioId || !scenario) return;

        setRetrying(true);
        setRetryError(null);
        try {
            const instruction = retryInstruction.trim() || 'Mermaid図が描画できるように修正してください。';
            const updatedScenario = await retryScenarioDiagram(scenarioId, {
                mermaid: mermaidText,
                instruction,
                render_error: renderErrorDetail || diagramError || undefined
            });
            setScenario(updatedScenario);
            setRetryInstruction('');
            setDiagramError(null);
        } catch (error) {
            console.error(error);
            setRetryError('AIリトライに失敗しました。時間をおいて再実行してください。');
        } finally {
            setRetrying(false);
        }
    };

    return (
        <div className="topology-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div className="tabs" style={{ padding: '10px', borderBottom: '1px solid #ccc' }}>
                <button
                    onClick={() => setActiveTab('diagram')}
                    style={{
                        marginRight: '10px',
                        padding: '8px 16px',
                        backgroundColor: activeTab === 'diagram' ? '#007bff' : '#f0f0f0',
                        color: activeTab === 'diagram' ? 'white' : 'black',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    Diagram
                </button>
                <button
                    onClick={() => setActiveTab('scenario')}
                    style={{
                        marginRight: '10px',
                        padding: '8px 16px',
                        backgroundColor: activeTab === 'scenario' ? '#007bff' : '#f0f0f0',
                        color: activeTab === 'scenario' ? 'white' : 'black',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    Scenario
                </button>
                <button
                    onClick={() => setActiveTab('yaml')}
                    style={{
                        padding: '8px 16px',
                        backgroundColor: activeTab === 'yaml' ? '#007bff' : '#f0f0f0',
                        color: activeTab === 'yaml' ? 'white' : 'black',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    YAML
                </button>
            </div>

            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                {activeTab === 'diagram' && (
                    <div className="diagram-pane">
                        {diagramError ? (
                            <div className="retry-panel">
                                <div style={{ color: '#ff7b7b', marginBottom: '10px' }}>{diagramError}</div>
                                {renderErrorDetail && (
                                    <pre className="retry-error-detail">{renderErrorDetail}</pre>
                                )}
                                <textarea
                                    className="retry-input"
                                    value={retryInstruction}
                                    onChange={(e) => setRetryInstruction(e.target.value)}
                                    placeholder="AIへの修正指示を入力（この内容をそのまま渡します）"
                                />
                                <button
                                    className="retry-button"
                                    onClick={handleRetryDiagram}
                                    disabled={retrying}
                                >
                                    {retrying ? 'Retrying...' : 'AIで図を修正してリトライ'}
                                </button>
                                {retryError && (
                                    <>
                                        <div className="retry-error-text">{retryError}</div>
                                        <button
                                            className="retry-button retry-button-secondary"
                                            onClick={handleRetryDiagram}
                                            disabled={retrying}
                                        >
                                            {retrying ? 'Retrying...' : '再度リトライする'}
                                        </button>
                                    </>
                                )}
                            </div>
                        ) : diagramSvg ? (
                            <div className="diagram-square">
                                <div className="mermaid-wrapper" dangerouslySetInnerHTML={{ __html: diagramSvg }} />
                            </div>
                        ) : (
                            <div style={{ color: '#999' }}>Mermaid図を読み込み中です...</div>
                        )}
                    </div>
                )}
                {activeTab === 'scenario' && (
                    <div style={{ flex: 1, padding: '20px', overflow: 'auto', backgroundColor: '#ffffff', color: '#111827' }}>
                        {scenario ? (
                            <div
                                style={{
                                    lineHeight: '1.8',
                                    fontSize: '14px',
                                    whiteSpace: 'pre-wrap'
                                }}
                            >
                                {scenario.description}
                            </div>
                        ) : (
                            <div style={{ color: '#666', fontStyle: 'italic' }}>
                                シナリオ情報がありません
                            </div>
                        )}
                    </div>
                )}
                {activeTab === 'yaml' && (
                    <div style={{ flex: 1, padding: '20px', overflow: 'auto', backgroundColor: '#ffffff', color: '#111827' }}>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                            {scenario?.yaml_content || 'No YAML content available.'}
                        </pre>
                    </div>
                )}
            </div>
        </div>
    );
}
