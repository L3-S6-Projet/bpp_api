from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q
from django.db.models.functions import Trunc
from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_ARRAY, TYPE_INTEGER, TYPE_STRING, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from pytz import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import Classroom, Occupancy
from scolendar.paginations import ClassroomResultSetPagination
from scolendar.serializers import ClassroomCreationSerializer, ClassroomSerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.common.schemas import occupancies_schema


class ClassroomViewSet(GenericAPIView, TokenHandlerMixin):
    serializer_class = ClassroomSerializer
    queryset = Classroom.objects.all()
    pagination_class = ClassroomResultSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('query', None)
        if query:
            if len(query) >= 3:
                queryset = queryset.filter(
                    Q(name__unaccent__icontains=query)
                )
        return queryset.order_by('name')

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all classrooms.',
        operation_description='Note : only users with the role `administrator`, or professors, should be able to access'
                              ' this route.\n10 classrooms should be returned per page. If less than three characters'
                              ' are provided for the query, it will not be applied.',
        responses={
            200: Response(
                description='A list of all classrooms.',
                schema=Schema(
                    title='ClassroomList',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING,
                                         example='success'),
                        'total': Schema(type=TYPE_INTEGER,
                                        description='Total number of classrooms',
                                        example=166),
                        'classrooms': Schema(type=TYPE_ARRAY,
                                             items=Schema(
                                                 title='Classroom',
                                                 type=TYPE_OBJECT,
                                                 properties={
                                                     'id': Schema(
                                                         type=TYPE_INTEGER,
                                                         example=166),
                                                     'name': Schema(
                                                         type=TYPE_STRING,
                                                         example='John'),
                                                     'capacity': Schema(
                                                         type=TYPE_INTEGER,
                                                         example=166),
                                                 }, required=['id', 'name', 'capacity', ]), ),
                    },
                    required=['status', 'total', 'classrooms', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
        },
        tags=['Classrooms', 'role-professor'],
        manual_parameters=[
            Parameter(name='query', in_=IN_QUERY, type=TYPE_STRING, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                result = self.get_paginated_response(serializer.data)
                response = result.data
            else:
                serializer = self.get_serializer(queryset, many=True)
                response = serializer.data
            data = {
                'status': 'success',
                'total': response['count'],
                'classrooms': response['results'],
            }
            return RF_Response(data)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except NotFound:
            data = {
                'status': 'success',
                'total': len(self.get_queryset()),
                'teachers': [],
            }
            return RF_Response(data)

    @swagger_auto_schema(
        operation_summary='Creates a new classroom.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            201: Response(
                description='Classroom created',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING,
                                         example='success'),
                    }, required=['status', ])),
            401: Response(
                description='Unauthorized access',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid capacity (code=`InvalidCapacity`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
        },
        tags=['Classrooms'],
        request_body=Schema(
            title='ClassroomCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='John'),
                'capacity': Schema(type=TYPE_INTEGER, example=166),
            }, required=['name', 'capacity', ]
        )
    )
    def post(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            serializer = ClassroomCreationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return RF_Response(serializer.data, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given classrooms using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'This request should be denied if the classroom is used in any occupancy.',
        responses={
            200: Response(
                description='Data deleted',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'success': Schema(
                            type=TYPE_STRING,
                            example='success'),
                    },
                    required=['success', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid ID(s) (code=`ClassroomUsed`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Classrooms'],
        request_body=Schema(
            title='IDRequest',
            type=TYPE_ARRAY,
            items=Schema(
                type=TYPE_INTEGER,
                example=166
            )
        ),
    )
    def delete(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)

            def delete_classroom(classroom_id: int):
                classroom = Classroom.objects.get(id=classroom_id)
                classroom.delete()

            for post_id in request.data:
                try:
                    delete_classroom(post_id)
                except Classroom.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)

            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ClassroomDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information for a classroom.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Teacher information',
                schema=Schema(
                    title='TeacherResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'classroom': Schema(
                            title='Classroom',
                            type=TYPE_OBJECT,
                            properties={
                                'id': Schema(type=TYPE_INTEGER, example=166),
                                'name': Schema(type=TYPE_STRING, example='B.001'),
                                'capacity': Schema(type=TYPE_STRING, example=166),
                            },
                            required=[
                                'id',
                                'name',
                                'capacity',
                            ]
                        ),
                    },
                    required=['status', 'classroom', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Classrooms', ]
    )
    def get(self, request, classroom_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                classroom = Classroom.objects.get(id=classroom_id)

                classroom = {
                    'id': classroom.id,
                    'name': classroom.name,
                    'capacity': classroom.capacity,
                }
                return RF_Response({'status': 'success', 'classroom': classroom})
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Updates information for a classroom.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'The omission of the `capacity` field is not an error : it should not be able to be '
                              'modified.',
        responses={
            200: Response(
                description='Data updated',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Classrooms', ],
        request_body=Schema(
            title='ClassroomUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='B.001'),
            },
            required=['name', ]
        )
    )
    def put(self, request, classroom_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                classroom = Classroom.objects.get(id=classroom_id)
                classroom.name = request.data['name']

                classroom.save()

                return RF_Response({'status': 'success', })
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ClassroomOccupancyViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a classroom for the given time period.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Classroom occupancies',
                schema=occupancies_schema,
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Classrooms', ],
        manual_parameters=[
            Parameter(
                name='start',
                description='Start timestamp of the occupancies',
                in_=IN_QUERY,
                type=TYPE_INTEGER,
                required=False,
            ),
            Parameter(
                name='end',
                description='End timestamp of the occupancies',
                in_=IN_QUERY,
                type=TYPE_INTEGER,
                required=False
            ),
            Parameter(
                name='occupancies_per_day',
                description='Pass 0 to return ALL the events',
                in_=IN_QUERY,
                type=TYPE_INTEGER,
                required=False
            ),
        ],
    )
    def get(self, request, classroom_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                classroom = Classroom.objects.get(id=classroom_id)

                def get_days() -> list:
                    start_timestamp = request.query_params.get('start', None)
                    end_timestamp = request.query_params.get('end', None)
                    nb_per_day = int(request.query_params.get('occupancies_per_day', 0))

                    days = []
                    occ = Occupancy.objects.filter(
                        classroom=classroom,
                        deleted=False
                    ).order_by('start_datetime').annotate(day=Trunc('start_datetime', 'day'))
                    if start_timestamp:
                        occ = occ.filter(
                            start_datetime__gte=datetime.fromtimestamp(
                                int(start_timestamp),
                                tz=timezone(settings.TIME_ZONE)
                            )
                        )
                    if end_timestamp:
                        occ = occ.filter(
                            end_datetime__lte=datetime.fromtimestamp(
                                int(end_timestamp),
                                tz=timezone(settings.TIME_ZONE)
                            )
                        )
                    for day in (occ[0].day + timedelta(n) for n in
                                range((occ[len(occ) - 1].day - occ[0].day).days + 2)):
                        day_occupancies = occ.filter(start_datetime__day=day.day)
                        if len(day_occupancies) == 0:
                            continue
                        if nb_per_day != 0:
                            day_occupancies = day_occupancies[:nb_per_day]
                        occ_list = []
                        for o in day_occupancies:
                            event = {
                                'id': o.id,
                                'group_name': f'Groupe {o.group_number}',
                                'subject_name': o.subject.name,
                                'teacher_name': f'{o.teacher.first_name} {o.teacher.last_name}',
                                'start': o.start_datetime.timestamp(),
                                'end': o.end_datetime.timestamp(),
                                'occupancy_type': o.occupancy_type,
                                'name': o.name,
                            }
                            if o.subject:
                                event['class_name'] = o.subject._class.name
                            if o.classroom:
                                event['classroom_name'] = o.classroom.name
                            occ_list.append(event)
                        days.append({'date': day.strftime("%d-%m-%Y"), 'occupancies': occ_list})
                    return days

                return RF_Response({'status': 'success', 'days': get_days()})
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
