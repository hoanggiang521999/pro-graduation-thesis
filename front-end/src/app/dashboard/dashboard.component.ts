import { Component, AfterViewInit, OnInit, ViewChild } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { UIChart } from 'primeng/chart';
import { ReportService } from '../core/services/report.service';
import { BaseComponent } from '../shared/components/base-component/base-component.component';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction'
import { EventService } from '../core/services/eventservice';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})

export class DashboardComponent extends BaseComponent implements AfterViewInit, OnInit {
  formSearch: FormGroup;
  formConfig = {
    dateInWeek: [new Date()]
  };
  data: any;  // pie chart
  basicData: any;   // line chart
  basicOptions: any;
  rangeDates: Date[];
  // data line chart
  totalTimekeeping: any[];
  totalArrivalLate: any[];
  totalLeftEarly: any[];
  fromDate: Date = this.getMonday(new Date());
  toDate: Date = this.getSunday(new Date());

  events: any[];
  options: any;

  constructor(
    public reportService: ReportService,
    private eventService: EventService
  ) {
    super(null);
    this.formSearch = this.buildForm({}, this.formConfig);
    this.initLineChart();
    this.initPieChart();
  }

  // tslint:disable-next-line:typedef
  get f() {
    return this.formSearch.controls;
  }

  ngAfterViewInit(): void { }

  ngOnInit(): void {
    const tempTime = new Date();
    this.loadLineChart(tempTime);
    this.loadPieChart();
    // event full-calendar
    this.reportService.getEvents().subscribe(res => {
      this.events = res.data;
    });
    this.options = {
      plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
      defaultDate: new Date(),
      header: {
          left: 'prev,next',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      locale: 'vi',
      editable: true
    };
  }

  getMonday(d: Date) {
    const date = new Date(d);
    const day = d.getDay();
    const diff = d.getDate() - day + (day == 0 ? -6:1); // adjust when day is sunday
    return new Date(d.setDate(diff));
  }

  getSunday(d: Date) {
    const date = new Date(d);
    const day = d.getDay();
    const diff = d.getDate() - day + 7; // adjust when day is sunday
    return new Date(d.setDate(diff));
  }

  changeDate() {
    const time = new Date(this.formSearch.controls.dateInWeek.value);
    this.fromDate = this.getMonday(time);
    this.toDate = this.getSunday(time);
    this.loadLineChart(time);
  }

  loadLineChart(timeCheck: Date): void {
    this.reportService.getChart(this.getMonday(timeCheck), this.getSunday(timeCheck)).subscribe(res => {
      // line chart
      this.basicData = {
        labels: ['Th??? 2', 'Th??? 3', 'Th??? 4', 'Th??? 5', 'Th??? 6', 'Th??? 7', 'Ch??? nh???t'],
        datasets: [
            {
                label: 'T???ng s??? nh??n vi??n ch???m c??ng',
                data: res.data.listAttendance,
                fill: false,
                borderColor: '#42A5F5'
            },
            {
                label: 'T???ng s??? nh??n vi??n ?????n mu???n',
                data: res.data.listChecinLate,
                fill: false,
                borderColor: '#FFA726'
            },
            {
              label: 'T???ng s??? nh??n vi??n v??? s???m',
              data: res.data.listDepartureEarly,
              fill: false,
              borderColor: '#FF6384'
          }
        ]
      }
    });
  }

  initLineChart(): void {
    // line chart
    this.basicData = {
      labels: ['Th??? 2', 'Th??? 3', 'Th??? 4', 'Th??? 5', 'Th??? 6', 'Th??? 7', 'Ch??? nh???t'],
      datasets: [
          {
              label: 'T???ng s??? nh??n vi??n ch???m c??ng',
              data: [],
              fill: false,
              borderColor: '#42A5F5'
          },
          {
              label: 'T???ng s??? nh??n vi??n ?????n mu???n',
              data: [],
              fill: false,
              borderColor: '#FFA726'
          },
          {
            label: 'T???ng s??? nh??n vi??n v??? s???m',
            data: [],
            fill: false,
            borderColor: '#FF6384'
        }
      ]
    }
  }

  initPieChart(): void {
    // pie chart
    this.data = {
      labels: ['D?????i 18 tu???i', '18 - 30 tu???i', '31 - 40 tu???i', '41 - 50 tu???i' , 'Tr??n 50 tu???i'],
      datasets: [
        {
          data: [],
          backgroundColor: ['#00dbd8', '#FF6384', '#36A2EB', '#FFCE56', '#52d952'],
          hoverBackgroundColor: ['#00dbd8', '#FF6384', '#36A2EB', '#FFCE56', '#52d952']
        }]
    };
  }

  loadPieChart(): void {
    this.reportService.getEmployeeByAge().subscribe(res => {
      this.data = {
        labels: ['D?????i 18 tu???i', '18 - 30 tu???i', '31 - 40 tu???i', '41 - 50 tu???i' , 'Tr??n 50 tu???i'],
        datasets: [
          {
            data: res.data.listDataPieChart,
            backgroundColor: ['#00dbd8', '#FF6384', '#36A2EB', '#FFCE56', '#52d952'],
            hoverBackgroundColor: ['#00dbd8', '#FF6384', '#36A2EB', '#FFCE56', '#52d952']
          }]
      };
    })
  }
}
