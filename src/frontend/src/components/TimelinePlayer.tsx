import { useEffect } from 'react';
import './TimelinePlayer.css';

interface TimelinePlayerProps {
    time: number;
    setTime: React.Dispatch<React.SetStateAction<number>>;
    maxTime: number;
    isPlaying: boolean;
    setIsPlaying: (playing: boolean) => void;
}

export default function TimelinePlayer({
    time, setTime, maxTime, isPlaying, setIsPlaying
}: TimelinePlayerProps) {

    useEffect(() => {
        let interval: any;
        if (isPlaying) {
            interval = setInterval(() => {
                setTime((prev: number) => {
                    if (prev >= maxTime) {
                        setIsPlaying(false);
                        return maxTime;
                    }
                    return prev + 10; // 10ms step
                });
            }, 10);
        }
        return () => clearInterval(interval);
    }, [isPlaying, maxTime, setTime, setIsPlaying]);

    const togglePlay = () => setIsPlaying(!isPlaying);

    return (
        <div className="timeline-container">
            <div className="controls">
                <button onClick={togglePlay}>{isPlaying ? 'Pause' : 'Play'}</button>
                <span className="time-display">{Math.floor(time)} ms</span>
            </div>
            <input
                type="range"
                min="0"
                max={maxTime}
                value={time}
                onChange={(e) => setTime(Number(e.target.value))}
                className="timeline-slider"
            />
        </div>
    );
}
