'use client';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition'

const SpeechButton = () => {
    const {
        transcript,
        listening,
        resetTranscript,
        browserSupportsSpeechRecognition
    } = useSpeechRecognition();
    
    return (
        <div
            className="flex gap-3 flex-col items-center justify-center"
        >
            <p>Microphone: {listening ? 'on' : 'off'}</p>
            <div
                className='flex gap-2'
            >
                <button
                    onClick={SpeechRecognition.startListening}
                    className='px-3 p-1 bg-white rounded-3xl text-black'
                >
                    Start
                </button>
                <button
                    onClick={SpeechRecognition.stopListening}
                    className='px-3 p-1 bg-white rounded-3xl text-black'
                >
                    Stop
                </button>
                <button
                    onClick={resetTranscript}
                    className='px-3 p-1 bg-white rounded-3xl text-black'
                >
                    Reset
                </button>
            </div>
            <p>{transcript}</p>
        </div>
    );
}

export default SpeechButton;