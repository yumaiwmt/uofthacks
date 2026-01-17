import { motion, useMotionValue, useTransform } from 'motion/react';
import { Heart, X } from 'lucide-react';

interface SwipeCardProps {
  image: string;
  onSwipe: (direction: 'left' | 'right') => void;
}

export function SwipeCard({ image, onSwipe }: SwipeCardProps) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [0, 1, 1, 1, 0]);

  const handleDragEnd = (_event: any, info: any) => {
    if (Math.abs(info.offset.x) > 100) {
      const direction = info.offset.x > 0 ? 'right' : 'left';
      onSwipe(direction);
    }
  };

  return (
    <motion.div
      className="absolute w-full h-full cursor-grab active:cursor-grabbing"
      style={{
        x,
        rotate,
        opacity,
      }}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={handleDragEnd}
      initial={{ scale: 1, opacity: 1 }}
      exit={{ 
        x: x.get() > 0 ? 300 : -300,
        opacity: 0,
        transition: { duration: 0.3 }
      }}
    >
      <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-2xl bg-white">
        <img
          src={image}
          alt="Fashion item"
          className="w-full h-full object-cover"
          draggable={false}
        />
        
        {/* Like indicator */}
        <motion.div
          className="absolute top-8 right-8 border-4 border-green-500 text-green-500 px-6 py-3 rounded-lg rotate-12"
          style={{ opacity: useTransform(x, [0, 100], [0, 1]) }}
        >
          <Heart className="w-12 h-12" fill="currentColor" />
        </motion.div>

        {/* Dislike indicator */}
        <motion.div
          className="absolute top-8 left-8 border-4 border-red-500 text-red-500 px-6 py-3 rounded-lg -rotate-12"
          style={{ opacity: useTransform(x, [-100, 0], [1, 0]) }}
        >
          <X className="w-12 h-12" strokeWidth={3} />
        </motion.div>
      </div>
    </motion.div>
  );
}