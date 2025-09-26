import React from 'react';
import { format, isSameDay } from 'date-fns';
import { Event, Beneficiary } from './types';

interface BeneficiaryRowProps {
  beneficiary: Beneficiary;
  dates: Date[];
  events: Event[];
  onSlotClick: (date: Date) => void;
}

const BeneficiaryRow: React.FC<BeneficiaryRowProps> = ({
  beneficiary,
  dates,
  events,
  onSlotClick
}) => {
  return (
    <div className="flex">
      {dates.map((date, index) => {
        const dayEvents = events.filter(event => isSameDay(event.start, date));
        
        return (
          <div
            key={index}
            className="w-48 h-16 flex-shrink-0 border-r border-gray-200 last:border-r-0 relative"
            onClick={() => onSlotClick(date)}
          >
            {dayEvents.map(event => (
              <div
                key={event.id}
                className={`absolute top-1 left-1 right-1 p-1 rounded text-xs text-white
                  ${event.type === 'rendez-vous' ? 'bg-purple-600' : 'bg-green-600'}`}
                style={{
                  height: 'calc(100% - 8px)'
                }}
              >
                <div className="truncate">{event.title}</div>
                <div className="text-xs opacity-75">
                  {format(event.start, 'HH:mm')} - {format(event.end, 'HH:mm')}
                </div>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
};

export default BeneficiaryRow;