import Image from "next/image";
import SpeechButton from "./components/SpeechButton";

export default function Home() {

  return (
    <div className="py-10 flex flex-col items-center justify-center">
      <h1 className="text-5xl">Finpal</h1>
      <h2 className="text-xl">Your AI Financial Portfolio Advisor</h2>
      <SpeechButton />
    </div>
  );
}
