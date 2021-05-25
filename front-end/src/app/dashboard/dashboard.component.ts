import { Component, AfterViewInit, OnInit, ViewChild } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { UIChart } from 'primeng/chart';
import { ReportService } from '../core/services/report.service';
import { BaseComponent } from '../shared/components/base-component/base-component.component';

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

  constructor(
    public reportService: ReportService
  ) {
    super(null);
    this.formSearch = this.buildForm({}, this.formConfig);
    // pie chart
    this.data = {
      labels: ['18 - 30 tuổi', '31 - 40 tuổi', '41 - 50 tuổi' , 'Trên 50 tuổi'],
      datasets: [
        {
          data: [300, 50, 100, 20],
          backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#52d952'],
          hoverBackgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#52d952']
        }]
    };

    // line chart
    this.basicData = {
      labels: ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'],
      datasets: [
          {
              label: 'Tổng số nhân viên chấm công',
              data: [65, 59, 80, 81, 56, 55, 40],
              fill: false,
              borderColor: '#42A5F5'
          },
          {
              label: 'Tổng số nhân viên đến muộn',
              data: [28, 48, 40, 19, 86, 27, 90],
              fill: false,
              borderColor: '#FFA726'
          },
          {
            label: 'Tổng số nhân viên về sớm',
            data: [50, 40, 20, 11, 0, 5, 25],
            fill: false,
            borderColor: '#FF6384'
        }
      ]
    }
  }

  // tslint:disable-next-line:typedef
  get f() {
    return this.formSearch.controls;
  }

  ngAfterViewInit(): void { }

  ngOnInit(): void {}

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

  changeDate(evt) {
    console.log('ahihi  1', evt);
  }
}
