'use client';
import axios from 'axios';
import { useState } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition'

const SpeechButton = () => {
    const {
        transcript,
        listening,
        resetTranscript,
    } = useSpeechRecognition();
    
    const [loadingResponse, setLoadingResponse] = useState<boolean>(false);
    // TODO: plug error message in state and display
    const [errorMessage, setErrorMessage] = useState<string>();
    const [recommendationText, setRecommendationText] = useState<string>('');
    const [rationaleText, setRationaleText] = useState<string>('');


    const getAiResponse = async () => {
        console.log('running ai response')
        try {
            setLoadingResponse(true);
            const inputJSON = {
                text: transcript
            };
            console.log(inputJSON);
            setRecommendationText('test recommendation');
            setRationaleText('test rationale');
            // TODO: use the given API to interact with AI
            // const fakeResponse = await axios.post('endpoint', inputJSON);

            // setResponseText(fakeResponse.data.rationale);
        } catch(error) {
            console.log('error:', error);
        } finally {
            setLoadingResponse(false);
        }
    }

    const onClickStop = async () => {
        SpeechRecognition.stopListening()
        await getAiResponse();
    }
    
    return (
        <div
            className="mt-10 gap-3 flex flex-col items-center justify-center"
        >
            <p>Talk to Finpal and get feedback on your portfolio</p>
            <p>Microphone: {listening ? 'on' : 'off'}</p>
            <div
                className='flex gap-2'
            >
                <button
                    onClick={() => SpeechRecognition.startListening()}
                    className={
                        `px-3 p-1 bg-white rounded-3xl text-black`
                    }
                >
                    Start
                </button>
                <button
                    onClick={onClickStop}
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
            <p className='mt-5'>Voice Input</p>
            <p>{transcript}</p>
            <p className='mt-5'>Response</p>
            {loadingResponse 
                ? <p>thinking... </p>
                : (
                    <>
                        <p>{recommendationText}</p>
                        <p>{rationaleText}</p>
                    </>
                )
            }
        </div>
    );
}

export default SpeechButton;