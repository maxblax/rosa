import React, { useState, useEffect, useRef } from 'react';
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css';
import gantt from 'dhtmlx-gantt';
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import AddEventModal from './AddEventModal'; // Popover original pour ajouter un événement.

const mockVolunteers = [
  { id: '1', name: 'Jean Dupont' },
  { id: '2', name: 'Marie Martin' },
  { id: '3', name: 'Sophie Laurent' },
];

const mockEvents = [
  {
    id: '1',
    volunteerId: '1',
    title: 'Faire le point avec Mme Tremblay',
    start: new Date(2024, 2, 20, 9, 0),
    end: new Date(2024, 2, 20, 10, 0),
  },
  {
    id: '2',
    volunteerId: '2',
    title: 'Distribution alimentaire',
    start: new Date(2024, 2, 20, 14, 0),
    end: new Date(2024, 2, 20, 15, 0),
  },
  {
    id: '3',
    volunteerId: '3',
    title: 'Rendez-vous avec M. Dupuis',
    start: new Date(2024, 2, 21, 10, 0),
    end: new Date(2024, 2, 21, 11, 0),
  },
];

const CalendarPage: React.FC = () => {
  const [view, setView] = useState<'week' | 'month'>('week');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const ganttContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ganttContainer.current) {
      gantt.init(ganttContainer.current);
      gantt.clearAll();

      // Configure Gantt columns and scales
      gantt.config.columns = [
        { name: 'text', label: 'Bénévoles', tree: true, width: 120 },
      ];
      gantt.config.scale_unit = view === 'week' ? 'day' : 'month';
      gantt.config.date_scale = view === 'week' ? '%D %d %M' : '%F';
      gantt.config.subscales = view === 'week'
        ? [{ unit: 'hour', step: 1, date: '%H:%i' }]
        : [{ unit: 'day', step: 1, date: '%d' }];

      // Map data
      gantt.parse({
        data: mockEvents.map((event) => ({
          id: event.id,
          text: mockVolunteers.find((v) => v.id === event.volunteerId)?.name,
          start_date: event.start,
          end_date: event.end,
        })),
      });

      // Handle double-click (already works)
      gantt.attachEvent('onTaskDblClick', (id) => {
        const task = gantt.getTask(id);
        alert(`Événement : ${task.text}`);
        return true;
      });
    }
  }, [view]);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex gap-2">
          <button
            onClick={() => setView('week')}
            className={`px-4 py-2 rounded-md ${
              view === 'week'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Semaine
          </button>
          <button
            onClick={() => setView('month')}
            className={`px-4 py-2 rounded-md ${
              view === 'month'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Mois
          </button>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
        >
          <Plus size={20} />
          Ajouter un rendez-vous
        </button>
      </div>

      {/* Gantt Chart */}
      <div ref={ganttContainer} style={{ width: '100%', height: '600px' }} />

      {/* Modal for Adding Events */}
      {isModalOpen && (
        <AddEventModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          volunteers={mockVolunteers}
          onSave={(newEvent) => {
            mockEvents.push(newEvent);
            setIsModalOpen(false);
            gantt.render(); // Refresh Gantt chart.
          }}
        />
      )}
    </div>
  );
};

export default CalendarPage;