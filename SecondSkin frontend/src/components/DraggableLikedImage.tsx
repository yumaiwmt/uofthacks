import { useDrag } from 'react-dnd';
import { motion } from 'motion/react';

interface DraggableLikedImageProps {
  image: string;
  onRemove: () => void;
}

export function DraggableLikedImage({ image, onRemove }: DraggableLikedImageProps) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'FASHION_IMAGE',
    item: { image },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }));

  return (
    <motion.div
      ref={drag}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: isDragging ? 0.5 : 1 }}
      className="relative group cursor-move"
    >
      <img
        src={image}
        alt="Liked fashion item"
        className="w-full h-full object-cover rounded-lg shadow-lg"
        draggable={false}
      />
      <button
        onClick={onRemove}
        className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
      >
        <X className="w-4 h-4" />
      </button>
      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/30 rounded-lg transition-opacity">
        <p className="text-white text-sm font-medium">Drag to board</p>
      </div>
    </motion.div>
  );
}

function X({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}
