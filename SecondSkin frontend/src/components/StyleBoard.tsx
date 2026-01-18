import { useDrop } from 'react-dnd';
import { Trash2, Plus } from 'lucide-react';

interface StyleBoardProps {
  id: string;
  name: string;
  images: string[];
  onAddImage: (image: string) => void;
  onRemoveImage: (index: number) => void;
  onDelete: () => void;
  onRename: (newName: string) => void;
  onClick?: () => void;
}

export function StyleBoard({ 
  id, 
  name, 
  images, 
  onAddImage, 
  onRemoveImage,
  onDelete,
  onRename,
  onClick 
}: StyleBoardProps) {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: 'FASHION_IMAGE',
    drop: (item: { image: string }) => {
      onAddImage(item.image);
    },
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
    }),
  }));

  return (
    <div
      ref={drop}
      className={`flex-shrink-0 w-64 rounded-xl p-4 transition-all cursor-pointer ${
        isOver ? 'bg-pink-100 ring-2 ring-pink-500' : 'bg-gray-100 hover:bg-gray-200'
      }`}
      onClick={(e) => {
        // Only trigger onClick if not clicking on delete button or input
        const target = e.target as HTMLElement;
        if (!target.closest('button') && !target.closest('input')) {
          onClick?.();
        }
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <input
          type="text"
          value={name}
          onChange={(e) => onRename(e.target.value)}
          onClick={(e) => e.stopPropagation()}
          className="bg-transparent outline-none font-semibold text-gray-900 w-full mr-2"
        />
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1 hover:bg-gray-200 rounded-lg transition-colors"
        >
          <Trash2 className="w-4 h-4 text-gray-600" />
        </button>
      </div>
      
      <div className="grid grid-cols-2 gap-2 min-h-32">
        {images.map((image, index) => (
          <div key={index} className="relative group aspect-square">
            <img
              src={image}
              alt={`Style ${index + 1}`}
              className="w-full h-full object-cover rounded-lg"
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemoveImage(index);
              }}
              className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
        {images.length === 0 && (
          <div className="col-span-2 flex items-center justify-center h-32 text-gray-400 text-sm">
            Drag liked images here
          </div>
        )}
      </div>
    </div>
  );
}

function X({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}