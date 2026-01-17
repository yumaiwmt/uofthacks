import { Heart, Bookmark } from 'lucide-react';

interface CuratedFeedProps {
  images: string[];
  onLike: (image: string) => void;
}

export function CuratedFeed({ images, onLike }: CuratedFeedProps) {
  return (
    <div className="w-full px-4 py-8">
      <h2 className="text-2xl font-semibold mb-6 text-gray-900">Your Curated Feed</h2>
      
      {images.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p>Start swiping to build your personalized feed!</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {images.map((image, index) => (
            <div key={index} className="group relative aspect-[3/4] overflow-hidden rounded-lg shadow-lg">
              <img
                src={image}
                alt={`Curated item ${index + 1}`}
                className="w-full h-full object-cover transition-transform group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute bottom-4 left-4 right-4 flex gap-2">
                  <button
                    onClick={() => onLike(image)}
                    className="flex-1 bg-white/90 hover:bg-white text-gray-900 px-4 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
                  >
                    <Heart className="w-4 h-4" />
                    <span className="text-sm font-medium">Like</span>
                  </button>
                  <button className="bg-white/90 hover:bg-white text-gray-900 p-2 rounded-lg transition-colors">
                    <Bookmark className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
