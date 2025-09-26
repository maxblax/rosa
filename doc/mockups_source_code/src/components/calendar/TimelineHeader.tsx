import React from 'react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

interface TimelineHeaderProps {
  dates: Date[];
}

const TimelineHeader: React.FC<TimelineHeaderProps> = ({ dates }) => {
  return (
    <div className="flex">
      {dates.map((date, index) => (
        <div
          key={index}
          className="w-48 flex-shrink-0 p-3 text-sm font-medium text-gray-700 text-center border-r border-gray-200 last:border-r-0"
        >
          {format(date, 'EEEE d MMMM', { locale: fr })}
        </div>
      ))}
    </div>
  );
};

export default TimelineHeader;