import React, { useEffect, useRef } from 'react';
import "dhtmlx-gantt/codebase/dhtmlxgantt.css";
import gantt from 'dhtmlx-gantt';

interface GanttViewProps {
  events: {
    id: string;
    beneficiaryId: string;
    title: string;
    start: Date;
    end: Date;
    type: string;
  }[];
  onAddEvent: (start: Date, end: Date, beneficiaryId: string) => void;
  view: 'week' | 'month';
}

const GanttView: React.FC<GanttViewProps> = ({ events, onAddEvent, view }) => {
  const ganttContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ganttContainer.current) {
      gantt.init(ganttContainer.current);
      gantt.clearAll();

      // Configure Gantt timeline range based on view
      if (view === 'week') {
        gantt.config.scale_unit = 'day';
        gantt.config.date_scale = '%D, %d %M';
        gantt.config.scale_height = 50;
        gantt.config.subscales = [{ unit: 'hour', step: 1, date: '%H:%i' }];
      } else if (view === 'month') {
        gantt.config.scale_unit = 'week';
        gantt.config.date_scale = 'Semaine %W';
        gantt.config.subscales = [{ unit: 'day', step: 1, date: '%d %M' }];
      }

      // Map events to Gantt tasks
      gantt.parse({
        data: events.map((event) => ({
          id: event.id,
          text: event.title,
          start_date: event.start,
          end_date: event.end,
        })),
      });

      // Handle event creation
      gantt.attachEvent('onTaskCreated', (id) => {
        const task = gantt.getTask(id);
        onAddEvent(new Date(task.start_date), new Date(task.end_date), '');
        return true;
      });
    }
  }, [events, view]);

  return <div ref={ganttContainer} style={{ width: '100%', height: '600px' }} />;
};

export default GanttView;