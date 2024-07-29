import {useState} from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { SurveyComponent } from './multiStepForm.jsx';

function App() {
    const [count, setCount] = useState(0)

    return (
        <>
            <div className="container mx-auto p-4">
                <SurveyComponent/>
            </div>
        </>
    )
}

export default App
