import {LoaderIcon, Check} from 'lucide-react';


const Loader = ({className}) => {
    return (
        <LoaderIcon
            className={'h-4 w-4 animate-spin text-primary' + className}
        />
    );
};

export default function LoaderIcon() {
    function truncateFileName(fileName, maxLength = 15) {
        const parts = fileName.split('.');
        const extension = parts.pop(); // Extract extension
        let name = parts.join('.'); // Join back the rest in case multiple dots exist

        if (name.length > maxLength) {
            name = name.substring(0, maxLength) + '***'; // Truncate and add ellipsis
        }

        return `${name}.${extension}`;
    }

    return (props.status == 'COMPLETE' ? (
            <div className="flex flex-row h-5 space-x-2">
                <div>Audio {truncateFileName(props.filename)} Transcrit</div>
                <div><Check className="!size-4 text-green-500 mt-[1px]" strokeWidth={3}/></div>
            </div>
        ) : (
            <div className="flex flex-row h-5 space-x-2">
                <div>Audio {truncateFileName(props.filename)} en Cours de Transcription</div>
                <div><Loader className="!size-5"/></div>
            </div>
        )
    );
}